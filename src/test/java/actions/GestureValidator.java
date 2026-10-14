package actions;

import java.util.Set;

/** Pure argument validation for gestures; kept separate so it is testable without a device. */
public final class GestureValidator {

    public static final Set<String> DIRECTIONS = Set.of("up", "down", "left", "right");

    private GestureValidator() {
    }

    /** @return the normalised (lower-case) direction. */
    public static String validateDirection(String direction) {
        if (direction == null || !DIRECTIONS.contains(direction.trim().toLowerCase())) {
            throw new IllegalArgumentException("Direction must be one of " + DIRECTIONS + " but was '" + direction + "'");
        }
        return direction.trim().toLowerCase();
    }

    /** Percent must be in the half-open range (0, 1]. */
    public static double validatePercent(double percent) {
        if (Double.isNaN(percent) || percent <= 0.0 || percent > 1.0) {
            throw new IllegalArgumentException("Swipe percent must be in (0, 1] but was " + percent);
        }
        return percent;
    }

    public static int validateMaxAttempts(int attempts) {
        if (attempts < 1) {
            throw new IllegalArgumentException("maxAttempts must be >= 1 but was " + attempts);
        }
        return attempts;
    }
}
