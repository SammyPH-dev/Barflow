import type { RecommendationsResponse } from "./types";

// Request both recommendation lists from the backend.
export async function getRecommendations(baseUrl: string,):
 Promise<RecommendationsResponse> {
  const response = await fetch(
    `${baseUrl}/api/v1/recommendations/drinks`,
  );

  // Stop if the server returned an unsuccessful HTTP status.
  if (!response.ok) {
    throw new Error(
      `Unable to load recommendations (${response.status}).`,
    );
  }

  // Read the JSON response and return its contents.
  const data: RecommendationsResponse = await response.json();

  return data;
}