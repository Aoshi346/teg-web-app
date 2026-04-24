import type { ProjectStatus, ProjectType } from "@features/projects/types/project";

export type BreakdownSegment = {
  label: string;
  count: number;
  href: string;
};

export type ChipSegment = {
  label: string;
  count: number;
  href?: string;
};

export type TileTone =
  | "primary"
  | "accent"
  | "hero"
  | "blue"
  | "orange"
  | "green"
  | "amber";

export interface StatTileData {
  tone: TileTone;
  label: string;
  value: string;
  breakdown?: string;
  segments?: BreakdownSegment[];
  chips?: ChipSegment[];
  urgent?: boolean;
  href?: string;
}

export interface ListRowData {
  id: string | number;
  title: string;
  subtitle?: string;
  type?: ProjectType;
  status?: ProjectStatus | "upcoming";
  href?: string;
  hint?: string;
}

export type FeedItemKind = "submitted" | "reviewed" | "rejected" | "commented";

export interface FeedItemData {
  id: string | number;
  kind: FeedItemKind;
  text: string;
  time: string;
}

export interface SemesterMiniStat {
  num: string;
  label: string;
}

export interface DashboardContent {
  stats: StatTileData[];
  listTitle: string;
  listItems: ListRowData[];
  listEmpty: { text: string; hint?: string };
  feedItems: FeedItemData[];
  semesterStats?: SemesterMiniStat[];
}
