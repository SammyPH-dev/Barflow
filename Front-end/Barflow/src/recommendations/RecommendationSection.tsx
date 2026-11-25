import type { ReactNode } from "react";

type RecommendationSectionProps = {
  title: string;
  description: string;
  children: ReactNode;
};

/**
 * Displays the heading and explanation for a recommendation section.
 */
export default function RecommendationSection({
  title,
  description,
  children
}: RecommendationSectionProps) {
  return (
    <section className="recommendation-section">
        <h2>{title}</h2>
        <p>{description}</p>
        <div className="recommendation-grid">
            {children}
        </div>
    </section>
  );
}