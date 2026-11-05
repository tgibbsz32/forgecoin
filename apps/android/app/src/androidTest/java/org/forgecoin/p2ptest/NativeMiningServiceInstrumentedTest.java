package org.forgecoin.p2ptest;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.SystemClock;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Assume;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class NativeMiningServiceInstrumentedTest {
    private static final String QA_ADDRESS="YnJ4sygA2VbA4nvoXssZcSKh4fwsw4g3DaujrVCDXSwWGuXwnYTfNsKPVunwuAf8joPEWfePpMh6CEsyEqMpQz2i2uFy112XA";

    @Test public void directSoloReceivesAcceptedBlockAcknowledgment() {
        run("frgSoloEndpoint",0,false);
    }
    @Test public void privateStratumReportsAcceptedAndRejectedShares() {
        run("frgPoolEndpoint",2,true);
    }
    private static void run(String argument,int mode,boolean needRejected) {
        String endpoint=InstrumentationRegistry.getArguments().getString(argument);
        Assume.assumeTrue("An isolated loopback test endpoint is required",endpoint!=null);
        assertTrue(endpoint.startsWith("127.0.0.1:") && MiningConfiguration.isEligibleTestHost(endpoint));
        android.app.Instrumentation instrumentation=InstrumentationRegistry.getInstrumentation();
        Context context=instrumentation.getTargetContext();
        Activity activity=instrumentation.startActivitySync(new Intent(context,MainActivity.class)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        try {
            Intent intent=new Intent(context,MiningService.class).setAction(MiningService.START)
                .putExtra("address",QA_ADDRESS).putExtra("endpoint",endpoint)
                .putExtra("worker","android-qa").putExtra("mode",mode).putExtra("intensity",1)
                .putExtra("qaNodePort",Integer.parseInt(InstrumentationRegistry.getArguments()
                    .getString("frgQaNodePort","0")));
            context.startForegroundService(intent);
            long limit=SystemClock.elapsedRealtime()+100000;
            while(SystemClock.elapsedRealtime()<limit) {
                MiningStatistics stats=MiningService.statistics();
                if(stats.accepted()>0 && (!needRejected || stats.rejected()>0) &&
                   stats.hashesPerSecond(SystemClock.elapsedRealtime())>0)break;
                if(MiningService.status().startsWith("Miner start failed") ||
                   MiningService.logs().contains("Safety stop:") ||
                   MiningService.logs().contains("Mining refused:"))break;
                SystemClock.sleep(250);
            }
            MiningStatistics stats=MiningService.statistics();
            assertTrue(MiningService.logs(),stats.accepted()>0);
            if(needRejected)assertTrue(MiningService.logs(),stats.rejected()>0);
            assertTrue(MiningService.logs(),stats.hashesPerSecond(SystemClock.elapsedRealtime())>0);
        } finally {
            context.stopService(new Intent(context,MiningService.class));
            instrumentation.runOnMainSync(activity::finish);
        }
    }
}
