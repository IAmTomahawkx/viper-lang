from .. import objects

try:
    import aiohttp
except ImportError as e:
    raise Exception("aiohttp is required to use the requests module") from e


@objects.wraps_as_native("Fetches from an api. Takes a URL, and optionally an Authorization header. Returns a dictionary")
async def get_request(lineno, runner, url: objects.String, authorization: objects.String = None):
    if not runner.session:
        runner.session = aiohttp.ClientSession()

    url = url._value

    headers = {}
    if authorization is not None:
        headers['Authorization'] = authorization._value

    async with runner.session.get(url, headers=headers) as resp:
        status = resp.status
        text = await resp.text()

    return objects.PyObjectWrapper(runner, {
        "status": objects.Integer(status, runner, lineno),
        "response": objects.String(text, -1, runner)
    })


EXPORTS = {
    "get": get_request
}
MODULE_HELP = """
Module for making HTTP requests in viper. Still a WIP.
"""