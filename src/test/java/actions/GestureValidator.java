package actions;

import java.util.Set;

/** Pure argument validation for gestures; kept separate so it is testable without a device. */
public final class GestureValidator {

    public static final Set<String> DIRECTIONS = Set.of("up", "down", "left", "right");

    /** Utility class; not instantiable. */
    private GestureValidator() {
    }

    /**
     * Checks that a swipe direction is one of {@link #DIRECTIONS}, ignoring case and surrounding spaces.
     *
     * @param direction the requested direction
     * @return the normalised (lower-case, trimmed) direction
     * @throws IllegalArgumentException if the direction is null or unsupported
     */
    public static String validateDirection(String direction) {
        // Reject null or unknown values early so the device is never sent a bad gesture.
        if (direction == null || !DIRECTIONS.contains(direction.trim().toLowerCase())) {
            // Include the allowed set and the bad value so the caller can fix it quickly.
            throw new IllegalArgumentException("Direction must be one of " + DIRECTIONS + " but was '" + direction + "'");
        }
        // Return the normalised form that the mobile: swipeGesture command expects.
        return direction.trim().toLowerCase();
    }

    /**
     * Checks that a swipe percent is in the half-open range (0, 1].
     *
     * @param percent fraction of the swipe area to travel
     * @return the same value when valid
     * @throws IllegalArgumentException if the value is NaN, zero/negative or above 1
     */
    public static double validatePercent(double percent) {
        // NaN fails every comparison, so it must be checked explicitly alongside the range.
        if (Double.isNaN(percent) || percent <= 0.0 || percent > 1.0) {
            // Report the offending value to make misconfiguration obvious.
            throw new IllegalArgumentException("Swipe percent must be in (0, 1] but was " + percent);
        }
        // Hand back the validated value so calls can be chained.
        return percent;
    }

    /**
     * Checks that a retry/scroll bound allows at least one attempt.
     *
     * @param attempts maximum number of attempts
     * @return the same value when valid
     * @throws IllegalArgumentException if attempts is less than 1
     */
    public static int validateMaxAttempts(int attempts) {
        // Zero or negative bounds would make a scroll loop do nothing, so fail fast.
        if (attempts < 1) {
            // Report the offending value to make misconfiguration obvious.
            throw new IllegalArgumentException("maxAttempts must be >= 1 but was " + attempts);
        }
        // Hand back the validated value so calls can be chained.
        return attempts;
    }
}
