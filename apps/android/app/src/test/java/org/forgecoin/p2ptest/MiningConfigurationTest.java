package org.forgecoin.p2ptest;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.List;
public class MiningConfigurationTest {
    private static final String ADDRESS="YnJ4sygA2VbA4nvoXssZcSKh4fwsw4g3DaujrVCDXSwWGuXwnYTfNsKPVunwuAf8joPEWfePpMh6CEsyEqMpQz2i2uFy112XA";
    @Test public void rejectsProductionAndAmbiguousHosts(){
        for(String s:new String[]{"150.136.209.227:39481","8.8.8.8:39481","localhost:39481",
                "127.00.0.1:39481","256.0.0.1:5555","192.168.1.1:65536","172.32.0.1:5555","127.0.0.1:80"})
            assertFalse(s,MiningConfiguration.isEligibleTestHost(s));
    }
    @Test public void acceptsExplicitPrivateEndpoints(){
        for(String s:new String[]{"127.0.0.1:39481","192.168.1.10:5555","10.0.0.1:5555","172.16.0.1:5555"})
            assertTrue(s,MiningConfiguration.isEligibleTestHost(s));
    }
    @Test public void daemonSoloAndPoolUseCorrectProtocols(){
        List<String> solo=MiningConfiguration.buildCommand("miner",ADDRESS,"127.0.0.1:39481","qa",0,50,8);
        assertTrue(solo.contains("--daemon"));assertFalse(solo.contains("--keepalive"));
        List<String> pool=MiningConfiguration.buildCommand("miner",ADDRESS,"192.168.1.10:5555","qa",2,50,8);
        assertFalse(pool.contains("--daemon"));assertTrue(pool.contains("--keepalive"));
        assertTrue(pool.contains("--rig-id=qa"));assertTrue(pool.contains("--threads=2"));
        assertTrue(pool.contains("--algo=rx/0"));assertTrue(pool.contains("--randomx-mode=light"));
    }
    @Test public void usesCryptographicAddressChecksum(){
        try{MiningConfiguration.buildCommand("miner",ADDRESS.substring(0,97)+"B","127.0.0.1:39481","qa",0,50,8);fail();}
        catch(IllegalArgumentException expected){}
    }
    @Test public void intensityLeavesCpuHeadroom(){
        assertEquals(4,MiningConfiguration.threadsForIntensity(100,8));
        assertEquals(2,MiningConfiguration.threadsForIntensity(100,4));
        assertEquals(1,MiningConfiguration.threadsForIntensity(1,8));
        for(int[] p:new int[][]{{0,8},{101,8},{50,1}}){
            try{MiningConfiguration.threadsForIntensity(p[0],p[1]);fail();}
            catch(IllegalArgumentException expected){}
        }
    }
    @Test public void rejectsOptionAndShellInjection(){
        for(String worker:new String[]{"--url=host","a b","x;command","x\nother",""}){
            try{MiningConfiguration.sanitizeWorker(worker);fail();}
            catch(IllegalArgumentException expected){}
        }
    }
}
