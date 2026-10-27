//! Development-only miniFORGE atomic USDC / mFRG exchange.
//! Payment and delivery are executed as a single Solana transaction.
//! This program must NOT be used for a real sale without independent audit.

use anchor_lang::prelude::*;
use anchor_lang::solana_program::pubkey;
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token::{self, Mint, Token, TokenAccount, TransferChecked};

declare_id!("5NrwtM49RAn5iQicbod539qxhqYRkV3ZpiBudoUCUGNY");

pub const SALE_CAP_ATOMIC: u64 = 5_000_000_000_000;
const UNIT: u128 = 1_000_000;
const MAX_PRICE: u64 = 1_000_000_000_000;
const MAX_DURATION: i64 = 365 * 24 * 60 * 60;
#[cfg(not(feature = "devnet-only"))]
compile_error!("This contract is development-only; devnet-only feature required.");
// Local-mock-mints builds are for offline validator testing ONLY.
#[cfg(not(feature = "local-mock-mints"))]
const DEVNET_MFRG: Pubkey = pubkey!("9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw");

#[program]
pub mod miniforge_swap {
    use super::*;

    pub fn initialize_sale(
        ctx: Context<InitializeSale>,
        price_micro_usdc_per_mfrg: u64,
        max_buyer_atomic: u64,
        start_at: i64,
        end_at: i64,
    ) -> Result<()> {
        let now = Clock::get()?.unix_timestamp;
        require!(price_micro_usdc_per_mfrg > 0 && price_micro_usdc_per_mfrg <= MAX_PRICE,
            SwapError::InvalidPrice);
        require!(max_buyer_atomic > 0 && max_buyer_atomic <= SALE_CAP_ATOMIC,
            SwapError::InvalidBuyerCap);
        require!(end_at > start_at && end_at > now && start_at >= now.saturating_sub(300),
            SwapError::InvalidSaleWindow);
        require!(end_at.checked_sub(start_at).ok_or(SwapError::Overflow)? <= MAX_DURATION,
            SwapError::InvalidSaleWindow);
        require_keys_neq!(ctx.accounts.sale_mint.key(), ctx.accounts.usdc_mint.key(),
            SwapError::SameMint);
        require_eq!(ctx.accounts.sale_mint.decimals, 6, SwapError::WrongDecimals);
        require_eq!(ctx.accounts.usdc_mint.decimals, 6, SwapError::WrongDecimals);
        #[cfg(not(feature = "local-mock-mints"))]
        require_keys_eq!(ctx.accounts.sale_mint.key(), DEVNET_MFRG, SwapError::WrongDevnetMint);

        let s = &mut ctx.accounts.sale;
        s.admin = ctx.accounts.admin.key();
        s.sale_mint = ctx.accounts.sale_mint.key();
        s.usdc_mint = ctx.accounts.usdc_mint.key();
        s.vault = ctx.accounts.vault.key();
        s.treasury_usdc = ctx.accounts.treasury_usdc.key();
        s.price = price_micro_usdc_per_mfrg;
        s.buyer_cap = max_buyer_atomic;
        s.start_at = start_at;
        s.end_at = end_at;
        s.sold = 0;
        s.paused = true; // Explicit admin unpause required after funding
        s.bump = ctx.bumps.sale;
        emit!(SaleInitialized {
            sale: s.key(),
            price: s.price,
            start_at,
            end_at,
        });
        Ok(())
    }

    pub fn set_paused(ctx: Context<AdminControl>, paused: bool) -> Result<()> {
        ctx.accounts.sale.paused = paused;
        emit!(SalePauseChanged { sale: ctx.accounts.sale.key(), paused });
        Ok(())
    }

    // Price is immutable once the advertised start time has passed.
    pub fn set_price(ctx: Context<AdminControl>, price: u64) -> Result<()> {
        let s = &mut ctx.accounts.sale;
        require!(s.paused, SwapError::MustPause);
        require!(Clock::get()?.unix_timestamp < s.start_at, SwapError::PriceLocked);
        require!(price > 0 && price <= MAX_PRICE, SwapError::InvalidPrice);
        s.price = price;
        emit!(SalePriceChanged { sale: s.key(), price });
        Ok(())
    }

    pub fn purchase(ctx: Context<Purchase>, amount_atomic: u64, max_usdc_atomic: u64) -> Result<()> {
        let s = &mut ctx.accounts.sale;
        let now = Clock::get()?.unix_timestamp;
        require!(!s.paused, SwapError::Paused);
        require!(now >= s.start_at, SwapError::NotStarted);
        require!(now < s.end_at, SwapError::Ended);
        require!(amount_atomic > 0 && max_usdc_atomic > 0, SwapError::InvalidAmount);
        let new_sold = s.sold.checked_add(amount_atomic).ok_or(SwapError::Overflow)?;
        require!(new_sold <= SALE_CAP_ATOMIC, SwapError::CapExceeded);

        let rec = &mut ctx.accounts.buyer_record;
        if rec.buyer == Pubkey::default() {
            rec.buyer = ctx.accounts.buyer.key();
            rec.sale = s.key();
            rec.bought = 0;
            rec.bump = ctx.bumps.buyer_record;
        }
        require_keys_eq!(rec.buyer, ctx.accounts.buyer.key(), SwapError::WrongBuyer);
        require_keys_eq!(rec.sale, s.key(), SwapError::WrongBuyer);
        let new_bought = rec.bought.checked_add(amount_atomic).ok_or(SwapError::Overflow)?;
        require!(new_bought <= s.buyer_cap, SwapError::BuyerCapExceeded);
        let charge = quote_usdc_atomic(amount_atomic, s.price)?;
        require!(charge <= max_usdc_atomic, SwapError::SlippageExceeded);
        require!(ctx.accounts.vault.amount >= amount_atomic, SwapError::NotEnoughMfrg);
        require!(ctx.accounts.buyer_usdc.amount >= charge, SwapError::NotEnoughUsdc);

        // Buyer-authorized USDC debit (strictly immutable treasury destination).
        token::transfer_checked(CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            TransferChecked {
                from: ctx.accounts.buyer_usdc.to_account_info(),
                to: ctx.accounts.treasury_usdc.to_account_info(),
                mint: ctx.accounts.usdc_mint.to_account_info(),
                authority: ctx.accounts.buyer.to_account_info()
            }
        ), charge, 6)?;

        // Program escrow PDA authorizes mFRG delivery.
        // Failure reverts prior USDC transfer via Solana transaction atomicity.
        let bump = [s.bump];
        let seeds: &[&[&[u8]]] = &[&[b"sale", s.sale_mint.as_ref(), &bump]];
        token::transfer_checked(CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            TransferChecked {
                from: ctx.accounts.vault.to_account_info(),
                to: ctx.accounts.buyer_mfrg.to_account_info(),
                mint: ctx.accounts.sale_mint.to_account_info(),
                authority: s.to_account_info()
            },
            seeds
        ), amount_atomic, 6)?;

        s.sold = new_sold;
        rec.bought = new_bought;
        emit!(PurchaseCompleted {
            sale: s.key(), buyer: ctx.accounts.buyer.key(),
            mfrg_amount: amount_atomic, usdc_amount: charge,
            cumulative_sold: new_sold
        });
        Ok(())
    }

    // After the sale ENDS, paused admin may recover remaining escrow.
    pub fn withdraw_unsold(ctx: Context<WithdrawUnsold>, amount_atomic: u64) -> Result<()> {
        let s = &ctx.accounts.sale;
        require!(Clock::get()?.unix_timestamp >= s.end_at, SwapError::NotEnded);
        require!(s.paused, SwapError::MustPause);
        require!(amount_atomic > 0, SwapError::InvalidAmount);
        require!(ctx.accounts.vault.amount >= amount_atomic, SwapError::NotEnoughMfrg);
        let bump = [s.bump];
        let seeds: &[&[&[u8]]] = &[&[b"sale", s.sale_mint.as_ref(), &bump]];
        token::transfer_checked(CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            TransferChecked {
                from: ctx.accounts.vault.to_account_info(),
                to: ctx.accounts.admin_mfrg.to_account_info(),
                mint: ctx.accounts.sale_mint.to_account_info(),
                authority: s.to_account_info()
            },
            seeds
        ), amount_atomic, 6)?;
        emit!(UnsoldWithdrawn { sale: s.key(), amount: amount_atomic });
        Ok(())
    }
}

pub fn quote_usdc_atomic(amount_atomic: u64, price: u64) -> Result<u64> {
    require!(amount_atomic > 0 && price > 0, SwapError::InvalidAmount);
    let product = (amount_atomic as u128).checked_mul(price as u128).ok_or(SwapError::Overflow)?;
    let rounded = product.checked_add(UNIT - 1).ok_or(SwapError::Overflow)? / UNIT;
    require!(rounded <= u64::MAX as u128, SwapError::Overflow);
    Ok(rounded as u64)
}

#[derive(Accounts)]
pub struct InitializeSale<'info> {
    #[account(mut)] pub admin: Signer<'info>,
    #[account(mint::decimals = 6)] pub sale_mint: Account<'info, Mint>,
    #[account(mint::decimals = 6)] pub usdc_mint: Account<'info, Mint>,
    /// CHECK: Ownership is verified by the treasury_usdc token::authority constraint.
    pub treasury_owner: UncheckedAccount<'info>,
    #[account(token::mint = usdc_mint, token::authority = treasury_owner)]
    pub treasury_usdc: Account<'info, TokenAccount>,
    #[account(
        init, payer = admin, space = 8 + Sale::INIT_SPACE,
        seeds = [b"sale", sale_mint.key().as_ref()], bump
    )]
    pub sale: Account<'info, Sale>,
    #[account(
        init, payer = admin,
        associated_token::mint = sale_mint,
        associated_token::authority = sale
    )]
    pub vault: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct AdminControl<'info> {
    #[account(mut, has_one = admin @ SwapError::UnauthorizedAdmin)]
    pub sale: Account<'info, Sale>,
    pub admin: Signer<'info>,
}

#[derive(Accounts)]
pub struct Purchase<'info> {
    #[account(mut)] pub buyer: Signer<'info>,
    pub sale_mint: Account<'info, Mint>,
    pub usdc_mint: Account<'info, Mint>,
    #[account(mut,
        seeds = [b"sale", sale_mint.key().as_ref()], bump = sale.bump,
        has_one = sale_mint @ SwapError::WrongMint,
        has_one = usdc_mint @ SwapError::WrongMint,
        has_one = vault @ SwapError::WrongVault,
        has_one = treasury_usdc @ SwapError::WrongTreasury
    )]
    pub sale: Account<'info, Sale>,
    #[account(mut,
        associated_token::mint = sale_mint,
        associated_token::authority = sale
    )]
    pub vault: Account<'info, TokenAccount>,
    #[account(mut, token::mint = usdc_mint, token::authority = buyer)]
    pub buyer_usdc: Account<'info, TokenAccount>,
    #[account(mut, token::mint = sale_mint, token::authority = buyer)]
    pub buyer_mfrg: Account<'info, TokenAccount>,
    #[account(mut,
        token::mint = usdc_mint,
        address = sale.treasury_usdc @ SwapError::WrongTreasury
    )]
    pub treasury_usdc: Account<'info, TokenAccount>,
    #[account(
        init_if_needed, payer = buyer, space = 8 + BuyerRecord::INIT_SPACE,
        seeds = [b"buyer", sale.key().as_ref(), buyer.key().as_ref()], bump
    )]
    pub buyer_record: Account<'info, BuyerRecord>,
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct WithdrawUnsold<'info> {
    #[account(mut)] pub admin: Signer<'info>,
    pub sale_mint: Account<'info, Mint>,
    #[account(
        seeds = [b"sale", sale_mint.key().as_ref()], bump = sale.bump,
        has_one = admin @ SwapError::UnauthorizedAdmin,
        has_one = sale_mint @ SwapError::WrongMint,
        has_one = vault @ SwapError::WrongVault
    )]
    pub sale: Account<'info, Sale>,
    #[account(mut,
        associated_token::mint = sale_mint,
        associated_token::authority = sale
    )]
    pub vault: Account<'info, TokenAccount>,
    #[account(mut, token::mint = sale_mint, token::authority = admin)]
    pub admin_mfrg: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
}

#[account]
#[derive(InitSpace)]
pub struct Sale {
    pub admin: Pubkey,
    pub sale_mint: Pubkey,
    pub usdc_mint: Pubkey,
    pub vault: Pubkey,
    pub treasury_usdc: Pubkey,
    pub price: u64,
    pub buyer_cap: u64,
    pub start_at: i64,
    pub end_at: i64,
    pub sold: u64,
    pub paused: bool,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct BuyerRecord {
    pub buyer: Pubkey,
    pub sale: Pubkey,
    pub bought: u64,
    pub bump: u8,
}

#[event]
pub struct SaleInitialized {
    pub sale: Pubkey,
    pub price: u64,
    pub start_at: i64,
    pub end_at: i64,
}
#[event]
pub struct SalePauseChanged { pub sale: Pubkey, pub paused: bool }
#[event]
pub struct SalePriceChanged { pub sale: Pubkey, pub price: u64 }
#[event]
pub struct UnsoldWithdrawn { pub sale: Pubkey, pub amount: u64 }
#[event]
pub struct PurchaseCompleted {
    pub sale: Pubkey,
    pub buyer: Pubkey,
    pub mfrg_amount: u64,
    pub usdc_amount: u64,
    pub cumulative_sold: u64,
}

#[error_code]
pub enum SwapError {
    #[msg("Invalid unit price")] InvalidPrice,
    #[msg("Invalid buyer limit")] InvalidBuyerCap,
    #[msg("Invalid sale timestamps")] InvalidSaleWindow,
    #[msg("mFRG and USDC mints must differ")] SameMint,
    #[msg("Both token mints must have six decimals")] WrongDecimals,
    #[msg("Sale is paused")] Paused,
    #[msg("Sale has not started")] NotStarted,
    #[msg("Sale has ended")] Ended,
    #[msg("Sale has not ended")] NotEnded,
    #[msg("Purchase quantity must be positive")] InvalidAmount,
    #[msg("5M sale allocation exceeded")] CapExceeded,
    #[msg("Buyer cap exceeded")] BuyerCapExceeded,
    #[msg("Buyer maximum USDC debit exceeded")] SlippageExceeded,
    #[msg("Escrow lacks mFRG inventory")] NotEnoughMfrg,
    #[msg("Buyer lacks USDC")] NotEnoughUsdc,
    #[msg("Arithmetic overflow")] Overflow,
    #[msg("Only sale administrator is authorized")] UnauthorizedAdmin,
    #[msg("Wrong mFRG/USDC mint")] WrongMint,
    #[msg("Wrong escrow account")] WrongVault,
    #[msg("Wrong treasury account")] WrongTreasury,
    #[msg("Wrong buyer or buyer record")] WrongBuyer,
    #[msg("Sale must be paused")] MustPause,
    #[msg("Price is locked after sale start")] PriceLocked,
    #[msg("Unexpected devnet mFRG mint")] WrongDevnetMint,
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn quote_whole_tokens() {
        assert_eq!(quote_usdc_atomic(2_000_000, 50_000).unwrap(), 100_000);
        assert_eq!(quote_usdc_atomic(20_000_000, 1_000_000).unwrap(), 20_000_000);
    }
    #[test]
    fn fractional_token_ceil_prevents_free_tokens() {
        assert_eq!(quote_usdc_atomic(1, 1).unwrap(), 1);
        assert_eq!(quote_usdc_atomic(100_001, 50_000).unwrap(), 5_001);
        assert_eq!(quote_usdc_atomic(1_000_001, 50_000).unwrap(), 50_001);
    }
    #[test]
    fn supply_limit_matches_five_million() {
        assert_eq!(SALE_CAP_ATOMIC, 5_000_000 * 1_000_000);
    }
    #[test]
    fn rejects_zero_overflow() {
        assert!(quote_usdc_atomic(0, 1).is_err());
        assert!(quote_usdc_atomic(1, 0).is_err());
        assert!(quote_usdc_atomic(u64::MAX, u64::MAX).is_err());
    }
}
