package org.forgecoin.p2ptest;

import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Build;
import android.os.PowerManager;

/**
 * Read-only device diagnostics for a future bounded native RandomX miner.
 *
 * This class NEVER starts CPU work, bypasses thermal protections, accesses
 * wallet keys or grants mining capability. Any future worker must enforce its
 * own stop-on-thermal/low-battery/foreground-service policy independently.
 */
public final class MiningDeviceStatus {
    private MiningDeviceStatus() {}

    public static String summary(Context context) {
        if (context == null) return "Device status unavailable; mining disabled";
        String batteryText = "Battery unavailable";
        boolean charging = false;
        Intent battery = context.registerReceiver(
            null, new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        if (battery != null) {
            int level = battery.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
            int scale = battery.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
            int state = battery.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
            charging = state == BatteryManager.BATTERY_STATUS_CHARGING
                || state == BatteryManager.BATTERY_STATUS_FULL;
            if (level >= 0 && scale > 0 && level <= scale) {
                int percent = (int) ((long) level * 100L / scale);
                batteryText = "Battery " + percent + "% ("
                    + (charging ? "charging" : "not charging") + ")";
            }
        }
        PowerManager power = (PowerManager) context.getSystemService(
            Context.POWER_SERVICE);
        boolean powerSave = power != null && power.isPowerSaveMode();
        String thermal = "Thermal status unavailable";
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q && power != null) {
            thermal = thermalLabel(power.getCurrentThermalStatus());
        }
        int logicalCpu = Runtime.getRuntime().availableProcessors();
        return batteryText + "  |  " + thermal + "  |  "
            + (powerSave ? "Battery saver active" : "Battery saver off")
            + "  |  CPUs: " + logicalCpu;
    }

    public static String thermalLabel(int status) {
        switch (status) {
            case PowerManager.THERMAL_STATUS_NONE: return "Thermal: normal";
            case PowerManager.THERMAL_STATUS_LIGHT: return "Thermal: light";
            case PowerManager.THERMAL_STATUS_MODERATE: return "Thermal: moderate";
            case PowerManager.THERMAL_STATUS_SEVERE: return "Thermal: severe";
            case PowerManager.THERMAL_STATUS_CRITICAL: return "Thermal: critical";
            case PowerManager.THERMAL_STATUS_EMERGENCY: return "Thermal: emergency";
            case PowerManager.THERMAL_STATUS_SHUTDOWN: return "Thermal: shutdown";
            default: return "Thermal status unavailable";
        }
    }
}
