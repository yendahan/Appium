package exceptions;

/** Unchecked exception for framework-level failures; always carries context about what was attempted. */
public class FrameworkException extends RuntimeException {

    /**
     * Creates a framework failure with a descriptive message.
     *
     * @param message what was attempted and why it failed
     */
    public FrameworkException(String message) {
        // Delegate to RuntimeException so the message appears in stack traces and TestNG reports.
        super(message);
    }

    /**
     * Creates a framework failure that wraps the underlying error.
     *
     * @param message what was attempted and why it failed
     * @param cause   the original exception, preserved for root-cause diagnosis
     */
    public FrameworkException(String message, Throwable cause) {
        // Keep the original cause chained so the real failure is not lost when rethrowing.
        super(message, cause);
    }
}
