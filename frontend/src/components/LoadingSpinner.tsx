/**
 * Loading Spinner Component
 */

import './LoadingSpinner.css';

interface LoadingSpinnerProps {
    size?: 'small' | 'medium' | 'large';
    message?: string;
}

export default function LoadingSpinner({ size = 'medium', message }: LoadingSpinnerProps) {
    const sizeClass = `spinner-${size}`;

    return (
        <div className="loading-spinner-container">
            <div className={`spinner ${sizeClass}`}></div>
            {message && <p className="spinner-message">{message}</p>}
        </div>
    );
}
