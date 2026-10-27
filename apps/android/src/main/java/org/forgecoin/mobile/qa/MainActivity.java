package org.forgecoin.mobile.qa;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public final class MainActivity extends Activity {
    // QA-only: no spending keys, JNI wallet, miner service, Stratum, bridge or login.
    private static final String MONITOR = "https://150.136.209.227/pool/api/monitor";
    private static final String EXPLORER = "https://150.136.209.227/";
    private static final String GENESIS =
        "4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c";
    private static final int BG=Color.rgb(11,21,36);
    private static final int CARD=Color.rgb(21,38,58);
    private static final int TEXT=Color.rgb(224,237,247);
    private static final int SECONDARY=Color.rgb(168,191,211);
    private static final int ACCENT=Color.rgb(125,190,240);
    private static final int WARN=Color.rgb(252,192,118);
    private LinearLayout content;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        ScrollView scroller=new ScrollView(this);
        scroller.setFillViewport(true);
        scroller.setBackgroundColor(BG);
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(19),dp(23),dp(19),dp(26));
        scroller.addView(root);
        TextView brand=label("FORGECOIN",27,TEXT,true);
        root.addView(brand);
        root.addView(label("MOBILE  ·  READ-ONLY QA BUILD",11,ACCENT,true));
        root.addView(spacer(12));
        root.addView(note("PRELAUNCH: mining, FRG wallets, payouts and Solana functions are disabled. This APK does not hold cryptocurrency.",WARN));
        HorizontalScrollView tabs=new HorizontalScrollView(this);
        tabs.setHorizontalScrollBarEnabled(false);
        LinearLayout nav=new LinearLayout(this);
        nav.setOrientation(LinearLayout.HORIZONTAL);
        String[] titles={"Network","FRG Wallet","Solo","Pool","Solana"};
        for(final String title:titles){
            Button tab=button(title,true);
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,dp(48));
            lp.setMargins(0,dp(8),dp(7),dp(8));
            nav.addView(tab,lp);
            tab.setOnClickListener(v->render(title));
        }
        tabs.addView(nav);
        root.addView(tabs);
        content=new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        root.addView(content);
        root.addView(spacer(18));
        root.addView(label("Official network identity: FRG · genesis nonce 20261026 · P2P 39480 · RPC 39481",12,SECONDARY,false));
        root.addView(label("Source and QA tests: github.com/tgibbsz32/forgecoin. This preview must not be used to receive or mine real funds.",12,SECONDARY,false));
        setContentView(scroller);
        render("Network");
    }

    private void render(String tab){
        content.removeAllViews();
        content.addView(label(tab,24,TEXT,true));
        content.addView(spacer(9));
        switch(tab){
        case "Network":
            content.addView(note("Read-only Oracle telemetry. An active monitoring server is not proof that public mining has launched.",SECONDARY));
            final TextView network=note("Network status: not loaded",TEXT);
            content.addView(network);
            Button refresh=button("Refresh verified network status",true);
            content.addView(refresh);
            refresh.setOnClickListener(v->refreshStatus(network));
            Button explorer=button("Open the block explorer",true);
            content.addView(explorer);
            explorer.setOnClickListener(v->startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(EXPLORER))));
            refreshStatus(network);
            break;
        case "FRG Wallet":
            content.addView(note("COMING SOON — native Monero-derived FRG wallet integration is not implemented on Android. Recovery words, balances and encrypted keys do not exist in this app.",WARN));
            disabled("Create native FRG wallet");
            disabled("Open encrypted FRG wallet");
            disabled("Restore from 25-word FRG seed");
            disabled("Reveal recovery phrase");
            disabled("Export encrypted backup");
            disabled("Send / receive FRG");
            break;
        case "Solo":
            content.addView(note("Solo RandomX mining will connect to the verified 20261026 FRG daemon. Native RandomX/JNI execution and background service controls have not yet been implemented.",WARN));
            metric("Consensus", "RandomX CPU · 120-second target");
            metric("Genesis nonce", "20261026");
            metric("Starting difficulty", "500,000");
            disabled("Connect verified full node");
            disabled("Start solo mining");
            disabled("Stop solo mining");
            disabled("View solo mining logs");
            break;
        case "Pool":
            content.addView(note("The official FRG pool is not publicly operational. Its verified 1% fee is applied only to eligible pool-mined rewards. Solo miners pay no pool fee.",WARN));
            metric("Pool policy", "PPLNS · 1% operator fee · 99% miner distribution");
            metric("Pool share acceptance", "Validated on a disposable Oracle QA chain");
            disabled("Configure payout address");
            disabled("Add / rename worker");
            disabled("Connect to pool");
            disabled("Start pool mining");
            disabled("Show accepted / rejected shares");
            disabled("Change payout threshold");
            break;
        case "Solana":
            content.addView(note("Future mFRG SPL integration. No wallet, sale, bridge or token issuance is active on mobile.",WARN));
            disabled("Create Solana wallet");
            disabled("Restore Solana wallet");
            disabled("View SOL / mFRG balances");
            disabled("Backup Solana wallet");
            break;
        }
    }

    private void refreshStatus(final TextView view){
        view.setText("Checking HTTPS Oracle monitor…");
        new Thread(()->{
            String result;
            HttpURLConnection c=null;
            try{
                c=(HttpURLConnection)new URL(MONITOR).openConnection();
                c.setRequestMethod("GET");
                c.setConnectTimeout(5000);
                c.setReadTimeout(5000);
                c.setUseCaches(false);
                c.setRequestProperty("Accept","application/json");
                int status=c.getResponseCode();
                if(status!=200)throw new IllegalStateException("Monitor reports HTTP "+status+" (network offline/prelaunch)");
                try(InputStream in=c.getInputStream(); ByteArrayOutputStream bytes=new ByteArrayOutputStream()){
                    byte[] buf=new byte[1024];int count;
                    while((count=in.read(buf))!=-1){
                        bytes.write(buf,0,count);
                        if(bytes.size()>32768)throw new IllegalStateException("Monitor response too large");
                    }
                    JSONObject json=new JSONObject(bytes.toString("UTF-8"));
                    JSONObject net=json.optJSONObject("network");
                    if(net==null || !GENESIS.equals(net.optString("mainnetGenesis"))
                        || !"genesis-verified-prelaunch".equals(json.optString("status"))
                        || json.optBoolean("launchApproved",true)
                        || json.optBoolean("payoutsEnabled",true)
                        || json.optBoolean("miningAuthorized",true)
                        || Math.abs(System.currentTimeMillis()/1000-json.optLong("checkedAt",0))>120)
                        throw new IllegalStateException("Chain identity, timestamp or launch flags could not be verified");
                    result="Oracle genesis verified\n"
                        +"Current chain height: "+net.optLong("height",-1)+"\n"
                        +"Next difficulty: "+net.optLong("difficulty",-1)+"\n"
                        +"Connected peers: "+net.optLong("peers",-1)+"\n"
                        +"Public mining: DISABLED\n"
                        +"Payouts: DISABLED\n\n"
                        +"No balance or reward data is exposed through this monitor.";
                }
            }catch(Exception e){
                result="Oracle network unavailable or not launched.\n"+e.getClass().getSimpleName()
                       +": "+String.valueOf(e.getMessage());
            }finally{if(c!=null)c.disconnect();}
            final String update=result;
            runOnUiThread(()->{ if(!isFinishing() && view.getParent()!=null) view.setText(update); });
        },"ForgeCoin-QA-NodeCheck").start();
    }

    private int dp(float v){return Math.round(v*getResources().getDisplayMetrics().density);}
    private TextView label(String text,int size,int color,boolean bold){
        TextView label=new TextView(this);
        label.setText(text);label.setTextSize(size);label.setTextColor(color);
        label.setLineSpacing(dp(2),1.06f);
        if(bold)label.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return label;
    }
    private View spacer(int height){
        View view=new View(this);
        view.setLayoutParams(new LinearLayout.LayoutParams(1,dp(height)));
        return view;
    }
    private GradientDrawable background(int fill){
        GradientDrawable shape=new GradientDrawable();
        shape.setColor(fill);shape.setCornerRadius(dp(12));
        shape.setStroke(dp(1),Color.rgb(49,72,95));
        return shape;
    }
    private TextView note(String message,int color){
        TextView t=label(message,14,color,false);
        t.setPadding(dp(15),dp(15),dp(15),dp(15));
        t.setBackground(background(CARD));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.setMargins(0,dp(6),0,dp(12)); t.setLayoutParams(lp);
        return t;
    }
    private void metric(String name,String value){
        content.addView(label(name,12,SECONDARY,false));
        TextView v=label(value,15,TEXT,true);
        v.setPadding(0,dp(3),0,dp(12));content.addView(v);
    }
    private Button button(String title,boolean enabled){
        Button b=new Button(this);
        b.setText(title);b.setTextSize(12);b.setAllCaps(false);
        b.setTextColor(enabled?TEXT:SECONDARY);
        b.setBackground(background(enabled?Color.rgb(32,64,94):Color.rgb(29,38,50)));
        b.setEnabled(enabled);
        b.setPadding(dp(12),0,dp(12),0);
        return b;
    }
    private void disabled(String title){
        Button button=button(title+"  ·  unavailable",false);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(52));
        lp.setMargins(0,dp(5),0,dp(5));content.addView(button,lp);
    }
}
