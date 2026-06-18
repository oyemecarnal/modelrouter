/**
 * @raycast/api uses React 19 async-component patterns (FunctionComponents that
 * can return Promise<ReactNode>). @types/react@18.2.x provides the escape hatch
 * below for exactly this case. We also add bigint since @raycast/api's Key type
 * includes it.
 *
 * Plain `tsc --noEmit` outside of `ray build` needs these to avoid TS2786 errors.
 */
import "react";

declare module "react" {
  interface DO_NOT_USE_OR_YOU_WILL_BE_FIRED_EXPERIMENTAL_REACT_NODES {
    bigint: bigint;
    promise: Promise<ReactNode>;
  }
}
