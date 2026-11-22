# Exceptions

All exceptions derive from `NexarError`. HTTP-status errors derive from `RiotAPIError`,
which carries the status code and the server's message; `str(error)` renders as
`HTTP {status}: {message}`. The message is Riot's wording, so a 401 can arrive
saying `Forbidden`. Match on the exception type or the status code; the message text can mislead.

::: nexar.exceptions.NexarError

::: nexar.exceptions.RiotAPIError

::: nexar.exceptions.RateLimitError

::: nexar.exceptions.NotFoundError

::: nexar.exceptions.UnauthorizedError

::: nexar.exceptions.ForbiddenError

::: nexar.exceptions.BatchError
