/** First validation message the API returned for a form field, if any. */
export function fieldError(error, name) {
  return error?.fields?.[name]?.[0]
}
