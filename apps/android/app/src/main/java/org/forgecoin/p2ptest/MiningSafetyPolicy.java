package org.forgecoin.p2ptest;

/**
 * Pure CPU-miner resource policy; deliberately does not launch a worker.
 * A native miner must independently enforce stop limits in addition to this
 * UI preflight. No production mining runtime is authorized in this APK.
 */
public final class MiningSafetyPolicy {
    private MiningSafetyPolicy() {}

    /** Android PowerManager thermal statuses (0 none, 1 light, 2 moderate,
     * 3 severe, 4 critical, 5 emergency, 6 shutdown).
     */
    public static final int THERMAL_NONE = 0;
    public static final int THERMAL_LIGHT = 1;
    public static final int THERMAL_MODERATE = 2;
    public static final int THERMAL_SEVERE = 3;
    public static final int THERMAL_UNAVAILABLE = -1;
    public static final int MIN_BATTERY_PERCENT_UNPLUGGED = 20;
    public static final int MAX_CHARGING_CPU_PERCENT = 100;

    public static final class Recommendation {
        public final int threads;
        public final String reason;
        public final boolean eligible;

        private Recommendation(int threads, boolean eligible, String reason) {
            this.threads = threads;
            this.eligible = eligible;
            this.reason = reason;
        }
    }

    private static Recommendation stop(String reason) {
        return new Recommendation(0, false, reason);
    }

    /**
     * Fail closed on missing sensors, power constraints or build identity.
     * Thread counts are advisory, never an authorization to mine.
     *
     * @param runtimeApproved has an independently verified matching frozen FRG
     * native daemon, miner, wallet and release control (ALWAYS false in preview)
     * @param foregroundActive service is in an active, user-visible FGS state
     * @param allowScreenOff explicit opt-in to work while display is off
     */
    public static Recommendation evaluate(
            int availableCpus, int intensityPercent,
            int batteryPercent, boolean charging,
            boolean batterySaver, int thermalStatus,
            boolean foregroundActive, boolean screenInteractive,
            boolean allowScreenOff, boolean runtimeApproved) {
        if (!runtimeApproved) return stop("Native ARM64 FRG miner is not approved");
        if (!foregroundActive) return stop("Mining requires an active foreground service");
        if (availableCpus < 2) return stop("Insufficient CPU cores");
        if (intensityPercent < 1 || intensityPercent > 100)
            return stop("Invalid user mining intensity");
        if (batteryPercent < 0 || batteryPercent > 100)
            return stop("Battery status unavailable");
        if (batterySaver) return stop("Android battery saver is active");
        if (!charging && batteryPercent < MIN_BATTERY_PERCENT_UNPLUGGED)
            return stop("Battery below the unplugged safety threshold");
        if (!screenInteractive && !allowScreenOff)
            return stop("Screen-off mining not enabled by user");
        if (thermalStatus < THERMAL_NONE || thermalStatus > 6)
            return stop("Thermal status unavailable");
        if (thermalStatus >= THERMAL_SEVERE)
            return stop("Device thermal protection requires stopping");

        // Cap CPU use under warming conditions. Always preserve one core for UI.
        int limitedPercent = intensityPercent;
        if (thermalStatus == THERMAL_MODERATE)
            limitedPercent = Math.min(limitedPercent, 25);
        else if (thermalStatus == THERMAL_LIGHT)
            limitedPercent = Math.min(limitedPercent, 50);
        int cores = availableCpus - 1;
        int requested = Math.max(1, (int) (((long) cores * limitedPercent + 99) / 100));
        int threads = Math.min(cores, requested);
        return new Recommendation(threads, true,
            "Resource preflight only: " + threads + " thread(s) suggested; native miner still requires independent safeguards");
    }
}
