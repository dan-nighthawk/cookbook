import { YakYakClient } from "yakyak-sdk";

const client = new YakYakClient({
  baseUrl: "https://api.yakyak.ai",
  token: process.env.YAKYAK_API_TOKEN,
});

const styles = await client.data.getStyles();
console.log(styles);
