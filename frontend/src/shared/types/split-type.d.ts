declare module "split-type" {
  type SplitTypeTarget = string | Element | Element[] | NodeListOf<Element>;

  interface SplitTypeOptions {
    types?: string;
    tagName?: string;
    split?: string;
    lineClass?: string;
    wordClass?: string;
    charClass?: string;
    whitespace?: boolean | "collapse" | "preserve";
  }

  class SplitType {
    constructor(target: SplitTypeTarget, options?: SplitTypeOptions);
    chars: HTMLElement[];
    words: HTMLElement[];
    lines: HTMLElement[];
    original: string;
    revert(): void;
  }

  export default SplitType;
}

