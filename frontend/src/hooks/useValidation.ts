import { useState, useCallback } from "react";

type BannerType = "success" | "error" | "warning" | "info";

interface BannerState {
  visible: boolean;
  message: string;
  type: BannerType;
}

interface UseValidationReturn {
  bannerState: BannerState;
  showBanner: (message: string, type: BannerType) => void;
  closeBanner: () => void;
  bannerProps: {
    visible: boolean;
    message: string;
    type: BannerType;
    onClose: () => void;
    autoHide: number;
  };
}

/**
 * Custom hook for managing validation banner state
 * Provides consistent banner behavior across forms
 */
export function useValidation(): UseValidationReturn {
  const [bannerState, setBannerState] = useState<BannerState>({
    visible: false,
    message: "",
    type: "info",
  });

  const showBanner = useCallback((message: string, type: BannerType) => {
    setBannerState({
      visible: true,
      message,
      type,
    });
  }, []);

  const closeBanner = useCallback(() => {
    setBannerState((prev) => ({ ...prev, visible: false }));
  }, []);

  return {
    bannerState,
    showBanner,
    closeBanner,
    bannerProps: {
      visible: bannerState.visible,
      message: bannerState.message,
      type: bannerState.type,
      onClose: closeBanner,
      autoHide: 5000,
    },
  };
}
