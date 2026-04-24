import type { ProjectStatus, ProjectType } from "@features/projects/types/project";

export type BreakdownSegment = {
  label: string;
  count: number;
  href: string;
};

export interface StatTileData {
  tone: "primary" | "accent";
  label: string;
  value: string;
  breakdown?: string;
  segments?: BreakdownSegment[];
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

export interface DashboardContent {
  stats: StatTileData[];
  listTitle: string;
  listItems: ListRowData[];
  listEmpty: { text: string; hint?: string };
  feedItems: FeedItemData[];
}
