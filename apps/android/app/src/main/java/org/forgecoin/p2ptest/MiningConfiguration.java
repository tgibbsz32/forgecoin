package org.forgecoin.p2ptest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Recovered XMRig command builder, restricted to isolated QA until acceptance. */
public final class MiningConfiguration {
    private MiningConfiguration() {}
    public static boolean isEligibleTestHost(String text) {
        if(text==null || !text.matches("(?:[0-9]{1,3}\\.){3}[0-9]{1,3}:[0-9]{2,5}"))return false;
        String[] parts=text.split(":"); String[] segments=parts[0].split("\\.");
        int[] ip=new int[4];
        for(int i=0;i<4;i++) {
            ip[i]=Integer.parseInt(segments[i]);
            if(ip[i]>255 || (segments[i].length()>1 && segments[i].startsWith("0"))) return false;
        }
        int port=Integer.parseInt(parts[1]);
        if(port<1024 || port>65535)return false;
        return ip[0]==127 || ip[0]==10 || (ip[0]==172 && ip[1]>=16 && ip[1]<=31) ||
            (ip[0]==192 && ip[1]==168);
    }
    static int loopbackPort(String endpoint) {
        if(!isEligibleTestHost(endpoint) || !endpoint.startsWith("127.0.0.1:"))
            throw new IllegalArgumentException("Use a disposable loopback endpoint, 127.0.0.1:port");
        return Integer.parseInt(endpoint.substring("127.0.0.1:".length()));
    }
    public static int threadsForIntensity(int percent,int processors) {
        if(percent<1 || percent>100 || processors<2)
            throw new IllegalArgumentException("Invalid intensity or insufficient CPU cores");
        int max=Math.min(4,processors>=4?processors-2:processors-1);
        return Math.max(1,(max*percent+99)/100);
    }
    public static String sanitizeWorker(String worker) {
        if(worker==null || !worker.trim().matches("[A-Za-z0-9_-]{1,24}"))
            throw new IllegalArgumentException("Worker must contain 1-24 letters, digits, _ or -");
        return worker.trim();
    }
    public static List<String> buildCommand(String binary,String address,String endpoint,
            String worker,int mode,int percent,int cores) {
        if(!isEligibleTestHost(endpoint))throw new IllegalArgumentException("Private QA endpoint required");
        if(FrgPublicAddress.parse(address).kind!=FrgPublicAddress.Kind.STANDARD)
            throw new IllegalArgumentException("A native FRG standard mining address is required");
        if(mode<0 || mode>2)throw new IllegalArgumentException("Unknown mining mode");
        String rig=sanitizeWorker(worker);
        List<String> args=new ArrayList<>(Arrays.asList(binary,"--algo=rx/0","--url="+endpoint,
            "--user="+address,"--pass=x","--threads="+threadsForIntensity(percent,cores),
            "--cpu-priority=0","--randomx-mode=light","--no-huge-pages","--no-color","--no-title",
            "--print-time=15","--retries=2","--retry-pause=5","--donate-level=0","--randomx-init=1"));
        if(mode==0) {args.add("--daemon");args.add("--daemon-poll-interval=2000");}
        else {args.add("--rig-id="+rig);args.add("--keepalive");}
        return args;
    }
}
