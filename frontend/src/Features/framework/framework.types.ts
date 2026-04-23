export type FrameworkDocument = {
  user_document_id: string;
  framework: string;
  source_document: string;
  version: string;
  jurisdiction: string | null;
  chunk_count: number;
};

export type FrameworkIngest = {
  title: string;
  framework: string;
  version: string;
  jurisdiction?: string;
  text: string;
};
