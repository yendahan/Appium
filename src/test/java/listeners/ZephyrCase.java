package listeners;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/** Links a test method to a Zephyr Scale test case key (e.g. {@code BAY-T123}) so {@link ZephyrReporter} can publish its result. */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface ZephyrCase {
    /** The Zephyr test case key. */
    String value();
}
