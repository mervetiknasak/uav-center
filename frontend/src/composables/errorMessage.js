export function errorMessage(error, fallback) {
  return error instanceof Error ? error.message : fallback;
}
