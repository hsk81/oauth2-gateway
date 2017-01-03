# OAuth2 Gateway

Provides a gateway to allow *OAuth2* based authorization for a service, which
supports such a mechanism. Here is an abstract overview:

     +--------+                               +----------------+
     |        |--(A)- Authorization Request ->|    Resource    |
     |        |                               |      Owner     |
     |        |<-(B)-- Authorization Grant ---|                |
     |        |                               +----------------+
     |        |
     |        |                               +----------------+
     |        |--(C)-- Authorization Grant -->| Authorization  |
     | Client |                               |     Server     |
     |        |<-(D)----- Access Token -------|(oauth2-gateway)|
     |        |                               +----------------+
     |        |
     |        |                               +----------------+
     |        |--(E)----- Access Token ------>|    Resource    |
     |        |                               |     Server     |
     |        |<-(F)--- Protected Resource ---|                |
     +--------+                               +----------------+

The above diagram has been taken from the RFC of the [OAuth 2 Authorization Framework][2].

## Environment variables

The following parameters are required to be provided as environment variables:

### Mandatory environment variables

```bash
CLIENT_ID=
```

A client ID, which should have been issued when creating or registering your
integration with a particular service which uses *OAuth2*.

```bash
CLIENT_SECRET=
```

A client secret, which should have also been issued (along with the `CLIENT_ID`),
when creating or registering your integration with a particular service which 
uses *OAuth2*.

```bash
ACCESS_TOKEN_URI=
```

A URI (provided by the service in question), which will issue upon a successful
*authorization* an access token for *authentication* purposes.

```bash
REDIRECT_URI=
```

A redirection URI, where an instance of the `oauth2-gateway` should be living.
It will receive the access token upon successfully exchanging the corresponding
*authorization* code for the *authentication* access token.

```bash
REDIS_URL=
```

A URL to a `redis` instance, which will cache the issued access token for a
certain period of expiration time.

### Optional environment variables

```bash
DATETIME_PATH=/now
```

Path which allows to easily test if an `oauth2-gateway` instance is up and
running.

```bash
DEBUG=false
```

If set to `true` (or `1`) then the full POST request to the `ACCESS_TOKEN_URI`
will be logged: This should be used with care, since the *full* POST including
the `CLIENT_ID` and `CLIENT_SECRET` are logged!

```bash
GRANT_TYPE=authorization_code
```

Tells the access token issuing service behind the `ACCESS_TOKEN_URI` that we 
wish to acquire the token by providing an *authorization* code.

```bash
REDIS_EXPIRATION=1209600
```

The default expiration time of the cached access token in seconds, (which is
equal to `14` days).

## A concrete Authorization and Authentication Flow

1. Visit the *authorization* URL for a service to acquire the authorization
   code, with the `${AUTHORIZATION_URI}`:

```http
GET ${AUTHORIZATION_URI}
    ?client_id=${CLIENT_ID}
    &response_type=code
    &redirect_uri=${REDIRECT_URI}
    &scope=${SCOPE}
    &state=${STATE}
```

Where `${SCOPE}` should be a list of scopes we wish to be authorized for, and 
`${STATE}` is a random number (or string) which should be used for verification
purposes.

2. Once successfully authorized, the authorization service will redirect to the
   `${REDIRECT_URI}`:

```
GET ${REDIRECT_URI}
    ?code=${CODE}
    &state=${STATE}
```

3. The authorization `${CODE}` is issued by the authorization service, and will
   be used by `oauth2-gateway` to acquire the access token:

```
POST ${ACCESS_TOKEN_URI}
     ?client_id=${CLIENT_ID}
     &client_secret=${CLIENT_SECRET}
     &code=${CODE}
     &grant_type=${GRANT_TYPE}
     &redirect_uri=${REDIRECT_URI}
```

which should respond with a valid access token:

```json
{"access_token":"..", "expires_in": ".."}
```

which can then be used to access the service. Invoking the `${REDIRECT_URL}`
directly without an authorization `${CODE}` will either succeed or fail, which
is determined BY if an access token has already been cached (and not expired)
for a given `${STATE}`:

```
GET ${REDIRECT_URL}
    ?state=${STATE}
```

This can be used to ask `oauth2-gateway` for an access token by providing a
`${STATE}` (which has initially been used to acquire the access token in the
first place) *without* providing an authorization `${CODE}`.

## Additional information

The `oauth2-gateway` has been developed to integrate with [CISCO Spark][1], and
does *not* claim to support the full [OAuth 2 Authorization Framework][2].

## Author

Hasan Karahan, <hasan.karahan@blackhan.com>.

[1]: https://developer.ciscospark.com/authentication.html
[2]: https://tools.ietf.org/html/rfc6749
