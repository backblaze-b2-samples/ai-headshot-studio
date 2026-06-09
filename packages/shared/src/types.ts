export type FileStatus = "uploading" | "complete" | "error";

export interface FileMetadata {
  key: string;
  filename: string;
  folder: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
}

export interface FileMetadataDetail {
  filename: string;
  size_bytes: number;
  size_human: string;
  mime_type: string;
  extension: string;
  md5: string;
  sha256: string;
  uploaded_at: string;
  // Image-specific
  image_width: number | null;
  image_height: number | null;
  exif: Record<string, string> | null;
  // PDF-specific
  pdf_pages: number | null;
  pdf_author: string | null;
  pdf_title: string | null;
  // Audio/Video
  duration_seconds: number | null;
  codec: string | null;
  bitrate: number | null;
}

export interface FileUploadResponse {
  key: string;
  filename: string;
  size_bytes: number;
  size_human: string;
  content_type: string;
  uploaded_at: string;
  url: string | null;
  metadata: FileMetadataDetail | null;
}

export interface DailyUploadCount {
  date: string;
  uploads: number;
}

export interface UploadStats {
  total_files: number;
  total_size_bytes: number;
  total_size_human: string;
  uploads_today: number;
  total_downloads: number;
}

// --- Headshot studio domain ---

export type SubjectStatus =
  | "created"
  | "captioning"
  | "ready_to_train"
  | "training"
  | "trained"
  | "generating"
  | "complete"
  | "failed";

export interface SelfieRef {
  image_id: string;
  key: string;
  filename: string;
  caption: string | null;
}

export interface HeadshotRef {
  style_slug: string;
  key: string;
  index: number;
}

export interface Subject {
  id: string;
  name: string;
  status: SubjectStatus;
  created_at: string;
  updated_at: string;
  trigger_token: string;
  trainer_provider: string;
  generator_provider: string;
  selfies: SelfieRef[];
  styles_requested: string[];
  headshots: HeadshotRef[];
  lora_key: string | null;
  train_steps_done: number;
  train_steps_total: number;
  headshots_done: number;
  headshots_total: number;
  error: string | null;
}

export interface SubjectSummary {
  id: string;
  name: string;
  status: SubjectStatus;
  created_at: string;
  updated_at: string;
  selfie_count: number;
  headshot_count: number;
  cover_key: string | null;
}

export interface SubjectProgress {
  status: SubjectStatus;
  train_steps_done: number;
  train_steps_total: number;
  headshots_done: number;
  headshots_total: number;
  error: string | null;
}

export interface StylePack {
  slug: string;
  label: string;
  description: string;
  prompt_template: string;
  negative_prompt: string;
}

export interface HeadshotItem {
  key: string;
  style_slug: string;
  index: number;
  url: string;
}

export interface StyleSection {
  style: StylePack;
  headshots: HeadshotItem[];
}

export interface StorageSlice {
  category: string;
  size_bytes: number;
  size_human: string;
  object_count: number;
}

export interface StudioStats {
  subjects: number;
  headshots_generated: number;
  models_trained: number;
  storage_bytes: number;
  storage_human: string;
  breakdown: StorageSlice[];
}
