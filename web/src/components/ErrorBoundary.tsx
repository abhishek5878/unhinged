"use client";

import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[50vh] items-center justify-center px-4">
          <div className="w-full max-w-md text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-[#ef4444]/30 bg-[#ef4444]/5">
              <span className="text-lg text-[#ef4444]">!</span>
            </div>
            <h2 className="font-[family-name:var(--font-syne)] text-lg font-bold text-[#e8f4ff]">
              Something went wrong
            </h2>
            <p className="mt-2 font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/40">
              {this.state.error?.message || "An unexpected error occurred"}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="mt-6 rounded-lg border border-[#162638] px-6 py-2.5 font-[family-name:var(--font-syne)] text-xs font-bold text-[#e8f4ff]/60 transition-all hover:border-[#00c8ff]/30 hover:text-[#e8f4ff]"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
