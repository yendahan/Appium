package tests.unit;

import actions.GestureValidator;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertThrows;

/**
 * Device-free tests for GestureValidator, which checks swipe/scroll arguments before they reach the driver.
 * Side effects: none.
 */
// Class-level @Test puts every public method in the "unit" group, which is the default for `mvn test`.
@Test(groups = "unit")
public class GestureValidatorTest {

    /**
     * Supplies percent values that must be accepted.
     *
     * @return single-column rows covering the range (0, 1]: the smallest positive double, small, mid and the max
     */
    // Feeds acceptsBoundaryPercents.
    @DataProvider(name = "validPercents")
    public Object[][] validPercents() {
        // Lower boundary is exclusive of 0, so MIN_VALUE is the smallest legal input; 1.0 is the upper bound.
        return new Object[][]{{Double.MIN_VALUE}, {0.01}, {0.5}, {1.0}};
    }

    /**
     * Supplies percent values that must be rejected.
     *
     * @return single-column rows: zero, negative, just above 1, NaN and infinity
     */
    // Feeds rejectsOutOfRangePercents.
    @DataProvider(name = "invalidPercents")
    public Object[][] invalidPercents() {
        // Values just outside the range plus non-finite numbers.
        return new Object[][]{{0.0}, {-0.1}, {1.0000001}, {Double.NaN}, {Double.POSITIVE_INFINITY}};
    }

    /**
     * Scenario: percent values on and inside the valid range.
     * Assertion: validatePercent returns the same value unchanged.
     *
     * @param p a valid percent from the validPercents provider
     */
    // Runs once per valid value.
    @Test(dataProvider = "validPercents")
    public void acceptsBoundaryPercents(double p) {
        // Valid input must pass through untouched.
        assertEquals(GestureValidator.validatePercent(p), p);
    }

    /**
     * Scenario: percent values outside (0, 1] or not finite.
     * Assertion: validatePercent throws IllegalArgumentException.
     *
     * @param p an invalid percent from the invalidPercents provider
     */
    // Runs once per invalid value.
    @Test(dataProvider = "invalidPercents")
    public void rejectsOutOfRangePercents(double p) {
        // Bad input must be rejected before any gesture is sent to the device.
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validatePercent(p));
    }

    /**
     * Scenario: direction given with upper case and surrounding spaces.
     * Assertion: result is trimmed and lower-cased ("up").
     */
    public void normalisesDirectionCaseAndWhitespace() {
        // Callers may pass sloppy input; the validator returns the canonical form.
        assertEquals(GestureValidator.validateDirection("  UP "), "up");
    }

    /**
     * Scenario: null, empty and unsupported direction values.
     * Assertion: each throws IllegalArgumentException.
     */
    public void rejectsBadDirections() {
        // Null must not cause a NullPointerException.
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validateDirection(null));
        // Empty text is not a direction.
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validateDirection(""));
        // Only the supported directions are allowed; diagonals are not.
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validateDirection("diagonal"));
    }

    /**
     * Scenario: attempt counts around the lower boundary.
     * Assertion: 1 is accepted and returned; 0 and negative values throw IllegalArgumentException.
     */
    public void maxAttemptsBoundary() {
        // 1 is the smallest valid number of attempts.
        assertEquals(GestureValidator.validateMaxAttempts(1), 1);
        // Zero attempts would make the gesture do nothing.
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validateMaxAttempts(0));
        // Negative counts are invalid.
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validateMaxAttempts(-1));
    }
}
