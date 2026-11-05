package org.forgecoin.p2ptest;
import org.junit.Test;
import static org.junit.Assert.*;
public class MiningStatisticsTest {
    @Test public void countsAcknowledgedSharesWithoutDuplicatingLogs(){
        MiningStatistics s=new MiningStatistics();
        s.consume("cpu accepted (1/0) diff 1000 (12 ms)",0);
        s.consume("cpu accepted (1/0) diff 1000 (12 ms)",1);
        s.consume("cpu rejected (1/1) diff 1000 \"stale\" (12 ms)",2);
        s.consume("cpu accepted (2/1) diff 1000 (12 ms)",3);
        assertEquals(2,s.accepted());assertEquals(1,s.rejected());
    }
    @Test public void connectionFailuresAreNotRejectedShares(){
        MiningStatistics s=new MiningStatistics();s.consume("net connect error: refused",0);
        assertEquals(0,s.rejected());assertFalse(s.connected());
        assertTrue(Double.isNaN(s.hashesPerSecond(0)));
    }
    @Test public void reportsMeasuredHashrateAndExpiresIt(){
        MiningStatistics s=new MiningStatistics();
        s.consume("net new job from 127.0.0.1:5555 diff 1000 algo rx/0",0);
        s.consume("miner speed 10s/60s/15m 12.5 n/a n/a H/s max 13.2 H/s",1000);
        assertEquals(12.5,s.hashesPerSecond(1001),0);
        assertTrue(Double.isNaN(s.hashesPerSecond(46001)));
        s.disconnect();assertTrue(Double.isNaN(s.hashesPerSecond(2000)));
    }
    @Test public void handlesUnitsMissingWindowsAndReset(){
        MiningStatistics s=new MiningStatistics();s.consume("net new job from 10.0.0.1:5555",0);
        s.consume("miner speed 10s/60s/15m 1.25 1.2 n/a kH/s max 1.3 kH/s",0);
        assertEquals(1250,s.hashesPerSecond(10),0);
        s.consume("miner speed 10s/60s/15m n/a n/a n/a H/s",11);
        assertTrue(Double.isNaN(s.hashesPerSecond(12)));
        s.reset();assertEquals(0,s.accepted());assertFalse(s.connected());
        s.consume("miner speed 10s/60s/15m n/a n/a n/a H/s",10);
        assertTrue(Double.isNaN(s.hashesPerSecond(20)));
    }
}
