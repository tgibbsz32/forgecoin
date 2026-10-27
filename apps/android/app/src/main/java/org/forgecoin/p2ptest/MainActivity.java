package org.forgecoin.p2ptest;

import android.app.Activity;
import android.os.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.*;
import android.net.Uri;
import org.json.*;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import android.view.*;
import android.widget.*;

public class MainActivity extends Activity {
    private static final int NAVY=Color.rgb(7,16,27), PANEL=Color.rgb(17,30,43);
    private static final int CYAN=Color.rgb(61,224,208), BLUE=Color.rgb(87,152,255);
    private static final int WHITE=Color.rgb(241,247,252), MUTED=Color.rgb(160,175,190);
    private final Handler handler=new Handler(Looper.getMainLooper());
    private TextView status,logs;
    private LinearLayout newsItems;
    private static final String NEWS_URL="https://tgibbsz32.github.io/forgecoin/news.json";
    private void loadNews(){
        if(newsItems==null)return;
        newsItems.removeAllViews();newsItems.addView(label("Loading website announcements...",13,MUTED));
        new Thread(()->{
            try{
                HttpURLConnection con=(HttpURLConnection)new URL(NEWS_URL).openConnection();
                con.setConnectTimeout(6000);con.setReadTimeout(6000);con.setRequestProperty("Accept","application/json");
                if(con.getResponseCode()!=200)throw new IOException("HTTP "+con.getResponseCode());
                ByteArrayOutputStream out=new ByteArrayOutputStream();
                try(InputStream in=con.getInputStream()){
                    byte[] buf=new byte[4096];int n;while((n=in.read(buf))!=-1){out.write(buf,0,n);if(out.size()>131072)throw new IOException("Feed too large");}
                }finally{con.disconnect();}
                JSONArray items=new JSONObject(out.toString("UTF-8")).getJSONArray("updates");
                handler.post(()->{
                    if(newsItems==null)return;newsItems.removeAllViews();
                    if(items.length()==0)newsItems.addView(label("No announcements yet.",13,MUTED));
                    for(int i=0;i<Math.min(items.length(),20);i++){
                        JSONObject item=items.optJSONObject(i);if(item==null)continue;
                        String title=item.optString("title","Update"),date=item.optString("date",""),summary=item.optString("summary",""),url=item.optString("url","");
                        newsItems.addView(label(date+"  |  "+title,15,CYAN));newsItems.addView(label(summary,13,WHITE));
                        if(url.startsWith("https://tgibbsz32.github.io/forgecoin/"))link("Read more",url,newsItems);
                    }
                });
            }catch(Exception ex){handler.post(()->{if(newsItems!=null){newsItems.removeAllViews();newsItems.addView(label("News unavailable. Check your connection or open the website.",13,MUTED));link("Open ForgeCoin news","https://tgibbsz32.github.io/forgecoin/news.html",newsItems);}});}
        }).start();
    }
    private final Runnable refresh=new Runnable(){public void run(){
        if(status!=null)status.setText(NodeService.status);
        if(logs!=null)logs.setText(NodeService.logText());
        handler.postDelayed(this,2500);
    }};
    private GradientDrawable panelBackground(){
        GradientDrawable b=new GradientDrawable();b.setColor(PANEL);b.setCornerRadius(22);b.setStroke(1,Color.rgb(40,62,83));return b;
    }
    private TextView label(String s,int size,int color){
        TextView v=new TextView(this);v.setText(s);v.setTextColor(color);v.setTextSize(size);
        v.setPadding(0,8,0,8);return v;
    }
    private LinearLayout panel(LinearLayout main){
        LinearLayout p=new LinearLayout(this);p.setOrientation(1);p.setPadding(24,18,24,22);
        p.setBackground(panelBackground());
        LinearLayout.LayoutParams margins=new LinearLayout.LayoutParams(-1,-2);margins.setMargins(0,0,0,20);
        main.addView(p,margins);return p;
    }
    private Button button(String text,boolean enabled,LinearLayout parent,Runnable action){
        Button b=new Button(this);b.setText(text);b.setAllCaps(false);
        b.setTextColor(enabled?NAVY:MUTED);
        b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(enabled?CYAN:Color.rgb(46,59,74)));
        b.setEnabled(enabled);parent.addView(b);
        if(enabled&&action!=null)b.setOnClickListener(v->action.run());
        return b;
    }
    private void link(String title,String url,LinearLayout parent){
        button(title,true,parent,()->{
            try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(url)));}
            catch(Exception e){Toast.makeText(this,"No browser available",Toast.LENGTH_LONG).show();}
        });
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(NAVY);getWindow().setNavigationBarColor(NAVY);
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(NAVY);
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(22,20,22,40);scroll.addView(root);
        LinearLayout head=new LinearLayout(this);head.setOrientation(0);head.setGravity(Gravity.CENTER_VERTICAL);
        ImageView logo=new ImageView(this);logo.setImageResource(org.forgecoin.p2ptest.R.drawable.forgecoin_logo);
        logo.setScaleType(ImageView.ScaleType.FIT_CENTER);head.addView(logo,new LinearLayout.LayoutParams(88,88));
        LinearLayout brand=new LinearLayout(this);brand.setOrientation(1);brand.setPadding(14,0,0,0);
        brand.addView(label("FORGECOIN",25,WHITE));brand.addView(label("PRIVACY  /  CPU MINING",11,CYAN));
        head.addView(brand);root.addView(head);
        root.addView(label("Android miner & wallet",22,WHITE));
        root.addView(label("New-mainnet candidate — restricted testing. No public mining or wallet operations until the native runtime is validated.",13,MUTED));
        LinearLayout wallet=panel(root);wallet.addView(label("FRG WALLET",17,CYAN));
        wallet.addView(label("Secure wallet creation, seed restoration, balance scanning, send/receive and encrypted local storage are required for release.",13,WHITE));
        button("Create FRG wallet — unavailable",false,wallet,null);
        button("Restore FRG wallet — unavailable",false,wallet,null);
        button("Receive / send FRG — unavailable",false,wallet,null);
        LinearLayout mine=panel(root);mine.addView(label("RANDOMX MINING",17,CYAN));
        mine.addView(label("Solo and pool mining must use verified ARM64 RandomX executables and the frozen FRG chain identity.",13,WHITE));
        button("Start solo mining — unavailable",false,mine,null);
        button("Start pool mining — unavailable",false,mine,null);
        LinearLayout explore=panel(root);explore.addView(label("BLOCK EXPLORER & POOL STATS",17,CYAN));
        explore.addView(label("Read-only web tools. Statistics must be treated as unavailable until the production network and pool are validated.",13,MUTED));
        link("Pool dashboard", "https://tgibbsz32.github.io/forgecoin/pool.html",explore);
        link("Pool observer / statistics", "https://tgibbsz32.github.io/forgecoin/pool-observer.html",explore);
        link("Block explorer (staging)", "https://150.136.209.227/",explore);
        LinearLayout news=panel(root);news.addView(label("NEWS & UPDATES",17,CYAN));
        news.addView(label("Official announcements synced from the ForgeCoin website.",13,MUTED));
        newsItems=new LinearLayout(this);newsItems.setOrientation(1);news.addView(newsItems);
        button("Refresh news",true,news,()->loadNews());
        loadNews();
        LinearLayout node=panel(root);node.addView(label("NODE DIAGNOSTICS",17,CYAN));
        node.addView(label("Legacy ARM64 daemon is not certified for the October 26 mainnet. Remote node startup is disabled.",13,MUTED));
        status=label("Stopped",13,WHITE);node.addView(status);
        logs=label("",10,MUTED);logs.setTypeface(Typeface.MONOSPACE);node.addView(logs);
        LinearLayout solana=panel(root);solana.addView(label("SOLANA / mFRG — FUTURE RELEASE",17,BLUE));
        button("Solana wallet — unavailable",false,solana,null);
        button("mFRG balances / transfer — unavailable",false,solana,null);
        button("FRG staking — unavailable",false,solana,null);
        setContentView(scroll);
    }
    @Override protected void onResume(){super.onResume();handler.post(refresh);}
    @Override protected void onPause(){handler.removeCallbacks(refresh);super.onPause();}
}

[executed on device: TREYS_DELL_RTX (a6f7a031-77f9-48a0-8221-947182e0b72a)]