import type { AxiosRequestConfig } from "axios";

export type CreateClientConfig = (
  config: AxiosRequestConfig,
) => AxiosRequestConfig;
