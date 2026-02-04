// Document types
export interface Document {
  id: number;
  filename: string;
  original_image_path: string;
  enhanced_image_path: string | null;
  upload_date: string;
  status: 'uploaded' | 'enhanced' | 'segmented' | 'labeled' | 'trained' | 'processed';
}

// Character types
export interface BoundingBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Character {
  id: number;
  image_url: string;
  bbox: BoundingBox;
  label?: string;
  group_id?: number;
  is_valid?: boolean;
}

export interface CharacterGroup {
  [groupId: string]: Character[];
}

// Line types
export interface Line {
  id: number;
  line_order: number;
  image_url: string;
  text?: string;
  y_start: number;
  y_end: number;
}

// Enhancement parameters
export interface EnhancementParams {
  brightness: number;
  contrast: number;
  blur: number;
  threshold: number | null;
  sharpen: number;
}

// Training types
export interface TrainingStatus {
  is_training: boolean;
  current_epoch: number;
  total_epochs: number;
  loss: number;
  accuracy: number;
  num_samples: number;
  progress: number;
}

export interface TrainingModel {
  id: number;
  model_version: string;
  num_samples: number;
  accuracy: number;
  loss: number;
  trained_at: string;
}

// Batch processing types
export interface BatchJob {
  id: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_pages: number;
  processed_pages: number;
  created_at: string;
}

export interface BatchResult {
  id: number;
  document_id: number;
  extracted_text: string;
  confidence: number;
  created_at: string;
}

// API response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}
