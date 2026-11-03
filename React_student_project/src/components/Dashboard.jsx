
import StatCard from './StatCard';

function Dashboard() {
    const students = 25;
    const jobs = 12;
    const applications = 48;

    return (
        <main className="dashboard">
            <h2>Dashboard</h2>

            <div className="dashboard-cards">
                <StatCard
                    title="Total Students"
                    value={students}
                />

                <StatCard
                    title="Available Jobs"
                    value={jobs}
                />

                <StatCard
                    title="Applications"
                    value={applications}
                />
            </div>
        </main>
    );
}

export default Dashboard;
