// Logging utility for the frontend, sends logs to the backend
export type LogLevel = 'info' | 'warn' | 'error' | 'debug';

interface LogContext {
  [key: string]: any;
}

const BACKEND_LOG_URL = process.env.REACT_APP_BACKEND_URL
  ? process.env.REACT_APP_BACKEND_URL + '/frontend-log'
  : '/frontend-log';

export async function logToBackend(level: LogLevel, message: string, context: LogContext = {}) {
  try {
    await fetch(BACKEND_LOG_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ level, message, context }),
    });
  } catch (err) {
    // Fallback: log error to console
    // eslint-disable-next-line no-console
    console.error('Error sending log to backend:', err);
  }
}

// Convenience wrapper
export const frontendLogger = {
  info: (msg: string, ctx?: LogContext) => logToBackend('info', msg, ctx),
  warn: (msg: string, ctx?: LogContext) => logToBackend('warn', msg, ctx),
  error: (msg: string, ctx?: LogContext) => logToBackend('error', msg, ctx),
  debug: (msg: string, ctx?: LogContext) => logToBackend('debug', msg, ctx),
};
