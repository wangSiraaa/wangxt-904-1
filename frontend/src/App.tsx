import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, message } from 'antd'
import {
  HomeOutlined,
  BankOutlined,
  CalendarOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  FileTextOutlined,
  BarChartOutlined,
  AuditOutlined,
  LogoutOutlined,
  UserOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import StudyRooms from './pages/StudyRooms'
import Shifts from './pages/Shifts'
import Signups from './pages/Signups'
import Attendance from './pages/Attendance'
import LeaveRequests from './pages/LeaveRequests'
import Volunteers from './pages/Volunteers'
import Statistics from './pages/Statistics'
import AuditLogs from './pages/AuditLogs'

const { Header, Sider, Content } = Layout

function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [user, setUser] = useState<any>(null)
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    message.success('已退出登录')
    navigate('/login')
  }

  const getMenuItems = () => {
    const items: any[] = [
      {
        key: '/',
        icon: <HomeOutlined />,
        label: '首页',
      },
      {
        key: '/study-rooms',
        icon: <BankOutlined />,
        label: '书房点位',
      },
      {
        key: '/shifts',
        icon: <CalendarOutlined />,
        label: '班次管理',
      },
      {
        key: '/signups',
        icon: <FileTextOutlined />,
        label: '报名记录',
      },
      {
        key: '/attendance',
        icon: <CheckCircleOutlined />,
        label: '签到签退',
      },
      {
        key: '/leave',
        icon: <ThunderboltOutlined />,
        label: '请假补位',
      },
    ]

    if (user && (user.role === 'admin' || user.role === 'operations' || user.role === 'training')) {
      items.push({
        key: '/volunteers',
        icon: <TeamOutlined />,
        label: '志愿者管理',
      })
    }

    if (user && (user.role === 'admin' || user.role === 'operations')) {
      items.push({
        key: '/statistics',
        icon: <BarChartOutlined />,
        label: '运营统计',
      })
    }

    if (user && user.role === 'admin') {
      items.push({
        key: '/audit',
        icon: <AuditOutlined />,
        label: '审计日志',
      })
    }

    return items
  }

  const userMenu = {
    items: [
      {
        key: '1',
        label: user?.name || '用户',
        disabled: true,
      },
      {
        key: '2',
        label: user?.role === 'admin' ? '管理员' : user?.role === 'volunteer' ? '志愿者' : user?.role === 'operations' ? '运营人员' : '培训负责人',
        disabled: true,
      },
      {
        type: 'divider' as const,
      },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
        onClick: handleLogout,
      },
    ],
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: collapsed ? 14 : 18, fontWeight: 'bold', background: 'rgba(255,255,255,0.1)' }}>
          {collapsed ? '书房' : '城市书房排班'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={getMenuItems()}
          onClick={({ key }) => navigate(key as string)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 1px 4px rgba(0,21,41,.08)' }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>城市书房志愿排班系统</h2>
          <Dropdown menu={userMenu} placement="bottomRight">
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.name || '用户'}</span>
            </div>
          </Dropdown>
        </Header>
        <Content style={{ margin: '24px', padding: 24, background: '#fff', borderRadius: 8, minHeight: 280 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/study-rooms" element={<StudyRooms />} />
            <Route path="/shifts" element={<Shifts />} />
            <Route path="/signups" element={<Signups />} />
            <Route path="/attendance" element={<Attendance />} />
            <Route path="/leave" element={<LeaveRequests />} />
            <Route path="/volunteers" element={<Volunteers />} />
            <Route path="/statistics" element={<Statistics />} />
            <Route path="/audit" element={<AuditLogs />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

function PrivateRoute({ children }: { children: JSX.Element }) {
  const token = localStorage.getItem('token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <PrivateRoute>
              <AppLayout />
            </PrivateRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
