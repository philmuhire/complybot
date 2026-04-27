export type FrameworkDocument = {
  user_document_id: string;
  framework: string;
  source_document: string;
  version: string;
  jurisdiction: string | null;
  chunk_count: number;
  has_original?: boolean;
  original_filename?: string | null;
};

export type FrameworkIngest = {
  title: string;
  framework: string;
  version: string;
  jurisdiction?: string;
  /** Sent as JSON; merged on the server with `jurisdiction` */
  jurisdictions?: string[];
  text: string;
};
