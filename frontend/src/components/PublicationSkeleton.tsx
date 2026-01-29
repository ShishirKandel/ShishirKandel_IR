/**
 * Publication Skeleton Component
 * 
 * Shimmer loading placeholder for publication cards.
 */

import './PublicationSkeleton.css';

export default function PublicationSkeleton() {
    return (
        <div className="publication-skeleton">
            <div className="skeleton-title shimmer"></div>
            <div className="skeleton-authors shimmer"></div>
            <div className="skeleton-abstract">
                <div className="skeleton-line shimmer"></div>
                <div className="skeleton-line shimmer"></div>
                <div className="skeleton-line short shimmer"></div>
            </div>
            <div className="skeleton-meta">
                <div className="skeleton-date shimmer"></div>
                <div className="skeleton-link shimmer"></div>
            </div>
        </div>
    );
}
