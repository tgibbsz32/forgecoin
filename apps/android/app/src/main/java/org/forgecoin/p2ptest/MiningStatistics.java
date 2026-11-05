package org.forgecoin.p2ptest;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Session counters from XMRig 6.26 output; an accepted share is not a payout. */
public final class MiningStatistics {
    private static final Pattern RESULT=Pattern.compile("\\b(?:accepted|rejected) \\(([0-9]{1,18})/([0-9]{1,18})\\) diff ");
    private static final Pattern SPEED=Pattern.compile("\\bspeed 10s/60s/15m ([0-9]+(?:\\.[0-9]+)?) [^ ]+ [^ ]+ ([kM]?H/s)\\b");
    private long accepted,rejected,hashAt;
    private double hashRate=Double.NaN;
    private boolean connected;
    public synchronized void reset(){accepted=0;rejected=0;hashAt=0;hashRate=Double.NaN;connected=false;}
    public synchronized void consume(String line,long elapsedMillis) {
        if(line==null)return;
        String clean=line.replaceAll("\u001B\\[[0-9;]*[A-Za-z]","");
        Matcher m=RESULT.matcher(clean);
        if(m.find()) {
            long a=Long.parseLong(m.group(1)),r=Long.parseLong(m.group(2));
            // Never double-count a repeated diagnostic or regress session totals.
            accepted=Math.max(accepted,a);rejected=Math.max(rejected,r);
        }
        if(clean.contains("new job from "))connected=true;
        if(clean.contains("no active pools") || clean.contains("connect error") ||
           clean.contains("connection refused") || clean.contains("read error") ||
           clean.contains("connection reset"))disconnect();
        Matcher speed=SPEED.matcher(clean);
        if(speed.find()) {
            double value=Double.parseDouble(speed.group(1));
            if("kH/s".equals(speed.group(2)))value*=1000;
            if("MH/s".equals(speed.group(2)))value*=1000000;
            if(Double.isFinite(value) && value>=0){hashRate=value;hashAt=elapsedMillis;}
        } else if(clean.contains("speed 10s/60s/15m ")) {
            hashRate=Double.NaN;hashAt=0;
        }
    }
    public synchronized void disconnect(){connected=false;hashRate=Double.NaN;hashAt=0;}
    public synchronized long accepted(){return accepted;}
    public synchronized long rejected(){return rejected;}
    public synchronized boolean connected(){return connected;}
    public synchronized double hashesPerSecond(long now) {
        return connected && now>=hashAt && now-hashAt<=45000 ? hashRate : Double.NaN;
    }
}
