import { YakYakClient } from "yakyak-sdk";

const client = new YakYakClient({
  baseUrl: "https://api.yakyak.ai",
  token: process.env.YAKYAK_API_TOKEN,
});

// NOTE: this currently resolves to `undefined` because the OpenAPI spec declares
// no response body schema for this endpoint. Use the `...Raw` variant below to read
// the actual response until the spec gains proper response schemas.
const styles = await client.data.getStyles();
console.log(styles); // -> undefined until the spec defines a response schema

// To inspect the raw HTTP response in the meantime:
const raw = await client.data.getStylesRaw();
console.log("status:", raw.raw.status);
console.log("body:", await raw.raw.json().catch(() => "<non-JSON or empty body>"));
