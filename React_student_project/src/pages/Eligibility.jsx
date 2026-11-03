
import { useEffect, useState } from 'react';
import { getStudents } from '../services/studentService';
import { getJobs } from '../services/jobService';
import {
    checkEligibility,
    getEligibilityChecks,
} from '../services/eligibilityService';
import '../App.css';

// Safely handle normal arrays and paginated API responses.
function getList(data) {
    if (Array.isArray(data)) return data;

    return Array.isArray(data?.results) ? data.results : [];
}

function Eligibility() {
    const [students, setStudents] = useState([]);
    const [jobs, setJobs] = useState([]);
    const [studentId, setStudentId] = useState('');
    const [jobId, setJobId] = useState('');
    const [result, setResult] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [checking, setChecking] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        setLoading(true);
        setError('');

        try {
            const [studentData, jobData, historyData] =
                await Promise.all([
                    getStudents(),
                    getJobs(),
                    getEligibilityChecks(),
                ]);

            setStudents(getList(studentData));
            setJobs(getList(jobData));
            setHistory(getList(historyData));
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                'Unable to load eligibility data. Please check your API and permissions.'
            );
        } finally {
            setLoading(false);
        }
    }

    async function handleCheck(event) {
        event.preventDefault();

        if (!studentId || !jobId) {
            setError('Please select both a student and a job.');
            return;
        }

        setChecking(true);
        setError('');
        setResult(null);

        try {
            // Step 1: Perform the eligibility check.
            const data = await checkEligibility(studentId, jobId);

            // Keep the result even if history refresh fails.
            setResult(data);

            // Step 2: Refresh history separately.
            try {
                const updatedHistory = await getEligibilityChecks();
                setHistory(getList(updatedHistory));
            } catch (historyError) {
                console.error(
                    'Eligibility check succeeded, but history refresh failed:',
                    historyError
                );

                setError(
                    'Eligibility was checked successfully, but the history could not be refreshed. Please reload the page.'
                );
            }
        } catch (err) {
            setError(
                err.response?.data?.error ||
                err.response?.data?.detail ||
                (err.response?.data
                    ? JSON.stringify(err.response.data)
                    : '') ||
                'Unable to check eligibility.'
            );
        } finally {
            setChecking(false);
        }
    }

    if (loading) {
        return (
            <div className="page-container">
                <p>Loading eligibility data...</p>
            </div>
        );
    }

    return (
        <div className="eligibility-page">
            <div className="eligibility-header">
                <div>
                    <span className="eligibility-eyebrow">
                        PLACEMENT MANAGEMENT
                    </span>
                    <h1>Eligibility Engine</h1>
                    <p>
                        Check whether a student meets a job's eligibility requirements.
                    </p>
                </div>
            </div>

            {error && (
                <div className="eligibility-alert" role="alert">
                    <strong>Something went wrong</strong>
                    <p>{error}</p>
                </div>
            )}

            <section className="eligibility-card">
                <div className="eligibility-card-heading">
                    <div className="eligibility-icon">✓</div>
                    <div>
                        <h2>Check Student Eligibility</h2>
                        <p>
                            Select a student and job to evaluate eligibility criteria.
                        </p>
                    </div>
                </div>

                <form className="eligibility-form" onSubmit={handleCheck}>
                    <div className="eligibility-field">
                        <label htmlFor="eligibility-student">Student</label>
                        <select
                            id="eligibility-student"
                            value={studentId}
                            onChange={(event) => setStudentId(event.target.value)}
                            required
                        >
                            <option value="">Choose a student</option>

                            {students.map((student) => (
                                <option key={student.id} value={student.id}>
                                    {student.Name || student.name || `Student ${student.id}`}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="eligibility-field">
                        <label htmlFor="eligibility-job">Job</label>
                        <select
                            id="eligibility-job"
                            value={jobId}
                            onChange={(event) => setJobId(event.target.value)}
                            required
                        >
                            <option value="">Choose a job</option>

                            {jobs.map((job) => (
                                <option key={job.id} value={job.id}>
                                    {job.title} — Job #{job.id}
                                </option>
                            ))}
                        </select>
                    </div>

                    <button
                        type="submit"
                        className="eligibility-submit"
                        disabled={checking}
                    >
                        {checking
                            ? 'Checking eligibility...'
                            : 'Check Eligibility'}
                    </button>
                </form>
            </section>

            {result && (
                <section className="eligibility-card eligibility-result-card">
                    <div className="eligibility-card-heading">
                        <div>
                            <h2>Eligibility Result</h2>
                            <p>
                                Evaluation summary for the selected student and job.
                            </p>
                        </div>

                        <span
                            className={`eligibility-badge ${
                                result.is_eligible
                                    ? 'badge-success'
                                    : 'badge-danger'
                            }`}
                        >
                            {result.is_eligible
                                ? '✓ Eligible'
                                : '✕ Not Eligible'}
                        </span>
                    </div>

                    <div className="eligibility-result-details">
                        <div className="eligibility-detail">
                            <span>Student ID</span>
                            <strong>#{result.student}</strong>
                        </div>

                        <div className="eligibility-detail">
                            <span>Job ID</span>
                            <strong>#{result.job}</strong>
                        </div>

                        <div className="eligibility-detail">
                            <span>Checked at</span>
                            <strong>
                                {result.checked_at
                                    ? new Date(result.checked_at).toLocaleString()
                                    : 'Just now'}
                            </strong>
                        </div>
                    </div>

                    <div className="eligibility-reason">
                        <strong>Evaluation details</strong>
                        <p>{result.reason}</p>
                    </div>
                </section>
            )}

            <section className="eligibility-card">
                <div className="eligibility-card-heading history-heading">
                    <div>
                        <h2>Eligibility Check History</h2>
                        <p>Review previous eligibility evaluations.</p>
                    </div>

                    <span className="eligibility-count">
                        {history.length} records
                    </span>
                </div>

                {history.length === 0 ? (
                    <div className="eligibility-empty">
                        No eligibility checks found yet.
                    </div>
                ) : (
                    <div className="eligibility-table-wrapper">
                        <table className="eligibility-table">
                            <thead>
                                <tr>
                                    <th>Check ID</th>
                                    <th>Student</th>
                                    <th>Job</th>
                                    <th>Result</th>
                                    <th>Reason</th>
                                    <th>Checked At</th>
                                </tr>
                            </thead>

                            <tbody>
                                {history.map((item) => (
                                    <tr key={item.id}>
                                        <td>#{item.id}</td>
                                        <td>Student #{item.student}</td>
                                        <td>Job #{item.job}</td>
                                        <td>
                                            <span
                                                className={`eligibility-badge ${
                                                    item.is_eligible
                                                        ? 'badge-success'
                                                        : 'badge-danger'
                                                }`}
                                            >
                                                {item.is_eligible
                                                    ? 'Eligible'
                                                    : 'Not Eligible'}
                                            </span>
                                        </td>
                                        <td className="eligibility-reason-cell">
                                            {item.reason}
                                        </td>
                                        <td>
                                            {item.checked_at
                                                ? new Date(item.checked_at).toLocaleString()
                                                : '—'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </div>
    );
}

export default Eligibility;
