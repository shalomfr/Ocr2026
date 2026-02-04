import axios from 'axios';
import type {
  Document,
  CharacterGroup,
  Line,
  EnhancementParams,
  TrainingStatus,
  TrainingModel
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Upload APIs
export const uploadImage = async (file: File): Promise<{ document_id: number; image_url: string; filename: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });

  return response.data;
};

export const batchUpload = async (files: File[]): Promise<{
  uploaded: Array<{ document_id: number; image_url: string; filename: string }>;
  errors: string[];
}> => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  const response = await api.post('/api/batch/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });

  return response.data;
};

export const getDocument = async (documentId: number): Promise<Document> => {
  const response = await api.get(`/api/documents/${documentId}`);
  return response.data.document;
};

export const listDocuments = async (): Promise<Document[]> => {
  const response = await api.get('/api/documents');
  return response.data.documents;
};

export const deleteDocument = async (documentId: number): Promise<void> => {
  await api.delete(`/api/documents/${documentId}`);
};

// Enhancement APIs
export const enhanceImage = async (
  documentId: number,
  params: EnhancementParams
): Promise<{ image: string }> => {
  const response = await api.post('/api/enhance', {
    document_id: documentId,
    ...params
  });

  return response.data;
};

export const saveEnhancedImage = async (
  documentId: number,
  params: EnhancementParams
): Promise<{ image_url: string }> => {
  const response = await api.post('/api/enhance/save', {
    document_id: documentId,
    ...params
  });

  return response.data;
};

export const autoPreprocess = async (documentId: number): Promise<{ image: string }> => {
  const response = await api.post('/api/preprocess/auto', {
    document_id: documentId
  });

  return response.data;
};

// Segmentation APIs
export const segmentCharacters = async (
  documentId: number,
  options?: {
    min_area?: number;
    max_area?: number;
    clustering_method?: 'kmeans' | 'dbscan';
  }
): Promise<{ groups: CharacterGroup; total_characters: number; total_groups: number }> => {
  const response = await api.post('/api/segment/characters', {
    document_id: documentId,
    ...options
  });

  return response.data;
};

export const segmentLines = async (
  documentId: number,
  options?: {
    min_line_height?: number;
    method?: 'projection' | 'advanced';
  }
): Promise<{ lines: Line[]; total_lines: number }> => {
  const response = await api.post('/api/segment/lines', {
    document_id: documentId,
    ...options
  });

  return response.data;
};

export const getCharacters = async (documentId: number): Promise<CharacterGroup> => {
  const response = await api.get(`/api/characters/${documentId}`);
  return response.data.groups;
};

export const getLines = async (documentId: number): Promise<Line[]> => {
  const response = await api.get(`/api/lines/${documentId}`);
  return response.data.lines;
};

// Labeling APIs
export const labelCharacters = async (
  labels: Array<{ character_id: number; label: string; group_id?: number }>
): Promise<{ updated_count: number }> => {
  const response = await api.post('/api/label/characters', { labels });
  return response.data;
};

export const labelGroup = async (
  documentId: number,
  groupId: number,
  label: string
): Promise<{ updated_count: number }> => {
  const response = await api.post('/api/label/group', {
    document_id: documentId,
    group_id: groupId,
    label
  });

  return response.data;
};

export const transcribeLines = async (
  transcriptions: Array<{ line_id: number; text: string }>
): Promise<{ updated_count: number }> => {
  const response = await api.post('/api/transcribe/lines', { transcriptions });
  return response.data;
};

export const updateCharacter = async (
  characterId: number,
  updates: { label?: string; group_id?: number; is_valid?: boolean }
): Promise<void> => {
  await api.patch(`/api/character/${characterId}`, updates);
};

export const deleteCharacter = async (characterId: number): Promise<void> => {
  await api.delete(`/api/character/${characterId}`);
};

export const moveCharacter = async (
  characterId: number,
  newGroupId: number
): Promise<void> => {
  await api.post('/api/character/move', {
    character_id: characterId,
    new_group_id: newGroupId
  });
};

export const updateLine = async (lineId: number, text: string): Promise<void> => {
  await api.patch(`/api/line/${lineId}`, { text });
};

export const exportLabels = async (documentId: number): Promise<{
  characters: any[];
  lines: any[];
}> => {
  const response = await api.get(`/api/labels/export/${documentId}`);
  return response.data;
};

// Training APIs
export const startTraining = async (options?: {
  epochs?: number;
  batch_size?: number;
  learning_rate?: number;
}): Promise<{ num_samples: number; epochs: number }> => {
  const response = await api.post('/api/train', options);
  return response.data;
};

export const getTrainingStatus = async (): Promise<TrainingStatus> => {
  const response = await api.get('/api/train/status');
  return response.data.status;
};

export const startRetraining = async (options?: {
  document_ids?: number[];
  epochs?: number;
  learning_rate?: number;
}): Promise<{ num_new_samples: number }> => {
  const response = await api.post('/api/retrain', options);
  return response.data;
};

export const listModels = async (): Promise<TrainingModel[]> => {
  const response = await api.get('/api/models');
  return response.data.models;
};

export const getModel = async (modelId: number): Promise<TrainingModel> => {
  const response = await api.get(`/api/model/${modelId}`);
  return response.data.model;
};

export default api;
