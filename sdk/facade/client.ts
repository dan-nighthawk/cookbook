/* tslint:disable */
/* eslint-disable */
/**
 * Ergonomic client facade over the generated typescript-fetch output.
 * Hand-maintained and copied into the generated package at publish time (see
 * .github/workflows/publish-sdks.yml).
 */
import { Configuration, type ConfigurationParameters } from './runtime';
import { DataApi, SchedulerApi, SocialApi, UsersApi, WorkflowApi } from './apis/index';
import { Uploads } from './uploads';

export * from './uploads';

/**
 * Strips the generated `<tag>Controller` prefix from method names, so
 * `dataControllerGetStyles` is exposed simply as `getStyles` (and
 * `dataControllerGetStylesRaw` as `getStylesRaw`).
 */
export type Friendly<T> = {
  [K in keyof T as K extends `${string}Controller${infer R}` ? Uncapitalize<R> : K]: T[K];
};

const CONTROLLER_RE = /^[a-z][A-Za-z0-9]*Controller([A-Z].*)$/;

function friendly<T extends object>(api: T): any {
  const out: Record<string, unknown> = {};
  for (let proto: any = api; proto && proto !== Object.prototype; proto = Object.getPrototypeOf(proto)) {
    for (const key of Object.getOwnPropertyNames(proto)) {
      if (key === 'constructor' || key in out) continue;
      const value = (api as any)[key];
      const m = key.match(CONTROLLER_RE);
      const name = m ? m[1].charAt(0).toLowerCase() + m[1].slice(1) : key;
      out[name] = typeof value === 'function' ? value.bind(api) : value;
    }
  }
  return out;
}

export interface YakYakClientOptions extends ConfigurationParameters {
  /** Base URL of the API, e.g. "https://api.yakyak.ai". Alias for `basePath`. */
  baseUrl?: string;
  /** Bearer JWT (personal access token). Alias for `accessToken`. */
  token?: string;
  /** Default user id, used by uploads that need a `userId` field. */
  userId?: string;
}

export class YakYakClient {
  readonly config: Configuration;
  readonly data: Friendly<DataApi>;
  readonly workflow: Friendly<WorkflowApi>;
  readonly scheduler: Friendly<SchedulerApi>;
  readonly social: Friendly<SocialApi>;
  readonly users: Friendly<UsersApi>;
  /** Ergonomic multipart file uploads (see {@link Uploads}). */
  readonly uploads: Uploads;

  constructor(options: YakYakClientOptions = {}) {
    const { baseUrl, token, userId, basePath, accessToken, ...rest } = options;
    this.config = new Configuration({
      ...rest,
      basePath: basePath ?? baseUrl,
      accessToken: accessToken ?? token,
    });
    this.data = friendly(new DataApi(this.config));
    this.workflow = friendly(new WorkflowApi(this.config));
    this.scheduler = friendly(new SchedulerApi(this.config));
    this.social = friendly(new SocialApi(this.config));
    this.users = friendly(new UsersApi(this.config));
    const resolvedToken = token ?? (typeof accessToken === 'string' ? accessToken : undefined);
    this.uploads = new Uploads(basePath ?? baseUrl, resolvedToken, userId);
  }
}
