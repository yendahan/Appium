package tests.unit;

import actions.GestureValidator;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertThrows;

@Test(groups = "unit")
public class GestureValidatorTest {

    @DataProvider(name = "validPercents")
    public Object[][] validPercents() {
        return new Object[][]{{Double.MIN_VALUE}, {0.01}, {0.5}, {1.0}};
    }

    @DataProvider(name = "invalidPercents")
    public Object[][] invalidPercents() {
        return new Object[][]{{0.0}, {-0.1}, {1.0000001}, {Double.NaN}, {Double.POSITIVE_INFINITY}};
    }

    @Test(dataProvider = "validPercents")
    public void acceptsBoundaryPercents(double p) {
        assertEquals(GestureValidator.validatePercent(p), p);
    }

    @Test(dataProvider = "invalidPercents")
    public void rejectsOutOfRangePercents(double p) {
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validatePercent(p));
    }

    public void normalisesDirectionCaseAndWhitespace() {
        assertEquals(GestureValidator.validateDirection("  UP "), "up");
    }

    public void rejectsBadDirections() {
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validateDirection(null));
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validateDirection(""));
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validateDirection("diagonal"));
    }

    public void maxAttemptsBoundary() {
        assertEquals(GestureValidator.validateMaxAttempts(1), 1);
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validateMaxAttempts(0));
        assertThrows(IllegalArgumentException.class, () -> GestureValidator.validateMaxAttempts(-1));
    }
}
