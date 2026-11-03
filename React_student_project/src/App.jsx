
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';

import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

import AddStudent from './pages/AddStudent';
import EditStudent from './pages/EditStudent';
import Dashboard from './pages/Dashboard';
import Students from './pages/Students';
import StudentDetails from './pages/StudentDetails';
import Jobs from './pages/Jobs';
import Applications from './pages/Applications';
import NotFound from './pages/NotFound';
import Login from './pages/Login';
import AcademicRecords from './pages/AcademicRecords';
import AddAcademicRecord from './pages/AddAcademicRecord';
import Skills from './pages/Skills';
import Certifications from './pages/Certifications';
import Companies from './pages/Companies';
import PlacementDrives from './pages/PlacementDrives';
import Eligibility from './pages/Eligibility';
import Interviews from './pages/Interviews';
import Selections from './pages/Selections';
import SubjectSelection from './pages/SubjectSelection';
import SubjectConfiguration from './pages/SubjectConfiguration';
import UserManagement from './pages/UserManagement';
import SetPassword from './pages/SetPassword';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Courses from './pages/Courses';
import ProfileCorrectionRequests from './pages/ProfileCorrectionRequests';
import ProfileCorrections from './pages/ProfileCorrections';
import EligibilityCoordination from './pages/EligibilityCoordination';
import Notifications from './pages/Notifications';

import AdminDashboard from './pages/AdminDashboard';
import TeacherDashboard from './pages/TeacherDashboard';
import StudentDashboard from './pages/StudentDashboard';
import RegistrationOfficerDashboard from './pages/RegistrationOfficerDashboard';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* PUBLIC ROUTES */}
                <Route path="/login" element={<Login />} />
                <Route path="/set-password" element={<SetPassword />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />

                {/* ADMIN DASHBOARD */}
                <Route element={<ProtectedRoute allowedRoles={['Admin']} />}>
                    <Route path="/admin-dashboard" element={<Layout />}>
                        <Route index element={<AdminDashboard />} />
                    </Route>
                </Route>

                {/* TEACHER DASHBOARD */}
                <Route element={<ProtectedRoute allowedRoles={['Teacher']} />}>
                    <Route path="/teacher-dashboard" element={<Layout />}>
                        <Route index element={<TeacherDashboard />} />
                    </Route>
                </Route>

                {/* STUDENT DASHBOARD */}
                <Route element={<ProtectedRoute allowedRoles={['Student']} />}>
                    <Route path="/student-dashboard" element={<Layout />}>
                        <Route index element={<StudentDashboard />} />
                    </Route>
                </Route>

                {/* REGISTRATION OFFICER DASHBOARD */}
                <Route
                    element={
                        <ProtectedRoute allowedRoles={['Registration Officer']} />
                    }
                >
                    <Route path="/registration-officer-dashboard" element={<Layout />}>
                        <Route index element={<RegistrationOfficerDashboard />} />
                    </Route>

                    <Route path="/profile-corrections" element={<Layout />}>
                        <Route index element={<ProfileCorrectionRequests />} />
                    </Route>

                    <Route path="/eligibility-coordination" element={<Layout />}>
                        <Route index element={<EligibilityCoordination />} />
                    </Route>
                </Route>

                {/* SHARED APPLICATION LAYOUT */}
                <Route
                    element={
                        <ProtectedRoute
                            allowedRoles={[
                                'Admin',
                                'Teacher',
                                'Student',
                                'Registration Officer',
                            ]}
                        />
                    }
                >
                    <Route path="/" element={<Layout />}>
                        {/* General dashboard: Admin, Teacher and Student */}
                        <Route
                            element={
                                <ProtectedRoute
                                    allowedRoles={['Admin', 'Teacher', 'Student']}
                                />
                            }
                        >
                            <Route index element={<Dashboard />} />
                        </Route>

                        {/* STUDENTS: Admin, Teacher and Registration Officer */}
                        <Route
                            element={
                                <ProtectedRoute
                                    allowedRoles={[
                                        'Admin',
                                        'Teacher',
                                        'Registration Officer',
                                    ]}
                                />
                            }
                        >
                            <Route path="students" element={<Students />} />
                            <Route
                                path="students/:studentId"
                                element={<StudentDetails />}
                            />
                        </Route>

                        {/* ADD / EDIT STUDENTS: Admin only */}
                        <Route
                            element={<ProtectedRoute allowedRoles={['Admin']} />}
                        >
                            <Route path="students/add" element={<AddStudent />} />
                            <Route
                                path="students/:id/edit"
                                element={<EditStudent />}
                            />
                        </Route>

                        {/* JOBS: Admin, Teacher and Student */}
                        <Route
                            element={
                                <ProtectedRoute
                                    allowedRoles={['Admin', 'Teacher', 'Student','Registration Officer']}
                                />
                            }
                        >
                            <Route path="jobs" element={<Jobs />} />
                        </Route>

                        {/* APPLICATIONS: All four roles */}
                        <Route path="applications" element={<Applications />} />

                        {/* ACADEMIC RECORDS: All four roles can view */}
                        <Route
                            path="academic-records"
                            element={<AcademicRecords />}
                        />

                        {/* ADD ACADEMIC RECORD: Admin only */}
                        <Route
                            element={<ProtectedRoute allowedRoles={['Admin']} />}
                        >
                            <Route
                                path="academic-records/add"
                                element={<AddAcademicRecord />}
                            />
                        </Route>

                        {/* SKILLS: Student only */}
                        <Route
                            element={<ProtectedRoute allowedRoles={['Student']} />}
                        >
                            <Route path="skills" element={<Skills />} />
                        </Route>

                        {/* NOTIFICATIONS: Student only */}
                        <Route
                            element={<ProtectedRoute allowedRoles={['Student']} />}
                        >
                            <Route
                                path="notifications"
                                element={<Notifications />}
                            />
                        </Route>

                        {/* CERTIFICATIONS: All roles can access the page.
                            Page-level permissions must control editing. */}
                        <Route
                            path="certifications"
                            element={<Certifications />}
                        />

                        {/* COMPANIES: All four roles can view */}
                        <Route path="companies" element={<Companies />} />

                        {/* ADMIN-ONLY MANAGEMENT */}
                        <Route
                            element={<ProtectedRoute allowedRoles={['Admin']} />}
                        >
                            <Route
                                path="subject-configuration"
                                element={<SubjectConfiguration />}
                            />
                            <Route
                                path="user-management"
                                element={<UserManagement />}
                            />
                        </Route>

                        {/* COURSES: Admin and Teacher */}
                        <Route
                            element={
                                <ProtectedRoute
                                    allowedRoles={['Admin', 'Teacher']}
                                />
                            }
                        >
                            <Route path="courses" element={<Courses />} />
                        </Route>

                        {/* PLACEMENT DRIVES: All four roles */}
                        <Route
                            path="placement-drives"
                            element={<PlacementDrives />}
                        />

                        {/* ELIGIBILITY CHECKING: Teacher only */}
                        <Route
                            element={<ProtectedRoute allowedRoles={['Teacher']} />}
                        >
                            <Route
                                path="eligibility"
                                element={<Eligibility />}
                            />
                        </Route>

                        {/* INTERVIEWS: All four roles */}
                        <Route path="interviews" element={<Interviews />} />

                        {/* SELECTIONS: All four roles */}
                        <Route path="selections" element={<Selections />} />

                        {/* PROFILE CORRECTION REQUEST: Student and Teacher only */}
                        <Route
                            element={
                                <ProtectedRoute allowedRoles={['Student', 'Teacher']} />
                            }
                        >
                            <Route
                                path="profile-correction-request"
        element={<ProfileCorrections />}
    />
</Route>

                        {/* SUBJECT SELECTION: Student only */}
                        <Route
                            element={<ProtectedRoute allowedRoles={['Student']} />}
                        >
                            <Route
                                path="subject-selection"
                                element={<SubjectSelection />}
                            />
                        </Route>

                        {/* UNKNOWN ROUTES */}
                        <Route path="*" element={<NotFound />} />
                    </Route>
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;
