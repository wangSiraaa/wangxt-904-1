import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, List, Tag, message } from 'antd'
import {
  BankOutlined,
  CalendarOutlined,
  TeamOutlined,
  FileTextOutlined,
  AlertOutlined
} from '@ant-design/icons'
import { statsApi, shiftApi, signupApi } from '../api'
import dayjs from 'dayjs'

function Dashboard() {
  const [stats, setStats] = useState<any>(null)
  const [recentShifts, setRecentShifts] = useState<any[]>([])
  const [mySignups, setMySignups] = useState<any[]>([])
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const userStr = localStorage.getItem('user')
      const currentUser = userStr ? JSON.parse(userStr) : null

      if (currentUser && (currentUser.role === 'admin' || currentUser.role === 'operations')) {
        const statsRes = await statsApi.overview()
        setStats(statsRes.data)
      }

      const shiftsRes = await shiftApi.list({ status: 'published' })
      setRecentShifts(shiftsRes.data.slice(0, 5))

      if (currentUser && currentUser.role === 'volunteer') {
        const signupsRes = await signupApi.list()
        setMySignups(signupsRes.data.slice(0, 5))
      }
    } catch (error) {
      message.error('加载数据失败')
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'orange',
      approved: 'green',
      rejected: 'red',
      cancelled: 'default',
      published: 'blue',
      draft: 'default',
      full: 'orange',
      completed: 'green',
      morning: 'gold',
      afternoon: 'cyan',
      night: 'purple'
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待审核',
      approved: '已通过',
      rejected: '已拒绝',
      cancelled: '已取消',
      published: '已发布',
      draft: '草稿',
      full: '已满员',
      completed: '已完成',
      morning: '早班',
      afternoon: '午班',
      night: '晚班'
    }
    return texts[status] || status
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>工作台</h2>

      {stats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="书房点位"
                value={stats.total_rooms}
                prefix={<BankOutlined style={{ color: '#1890ff' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="班次总数"
                value={stats.total_shifts}
                prefix={<CalendarOutlined style={{ color: '#52c41a' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="志愿者"
                value={stats.total_volunteers}
                prefix={<TeamOutlined style={{ color: '#faad14' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="待审核报名"
                value={stats.pending_signups}
                prefix={<FileTextOutlined style={{ color: '#f5222d' }} />}
                valueStyle={{ color: stats.pending_signups > 0 ? '#f5222d' : undefined }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {stats && stats.replacement_todos > 0 && (
        <Card
          style={{ marginBottom: 24, borderLeft: '4px solid #faad14' }}
          bodyStyle={{ padding: 16 }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <AlertOutlined style={{ fontSize: 24, color: '#faad14' }} />
            <div>
              <div style={{ fontWeight: 'bold', fontSize: 16 }}>补位待办</div>
              <div style={{ color: '#666' }}>
                当前有 <b style={{ color: '#faad14' }}>{stats.replacement_todos}</b> 个补位待办需要处理
              </div>
            </div>
          </div>
        </Card>
      )}

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="近期班次" extra={<Tag color="blue">已发布</Tag>}>
            <List
              dataSource={recentShifts}
              renderItem={(item: any) => (
                <List.Item key={item.id}>
                  <List.Item.Meta
                    title={`${item.study_room?.name || '书房'} - ${dayjs(item.shift_date).format('MM月DD日')}`}
                    description={`${item.start_time?.slice(0, 5)} - ${item.end_time?.slice(0, 5)} | ${item.current_volunteers}/${item.max_volunteers}人`}
                  />
                  <Tag color={getStatusColor(item.shift_type)}>
                    {getStatusText(item.shift_type)}
                  </Tag>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        {user?.role === 'volunteer' && (
          <Col xs={24} lg={12}>
            <Card title="我的报名">
              {mySignups.length > 0 ? (
                <List
                  dataSource={mySignups}
                  renderItem={(item: any) => (
                    <List.Item key={item.id}>
                      <List.Item.Meta
                        title={`班次 #${item.shift_id}`}
                        description={dayjs(item.signup_time).format('YYYY-MM-DD HH:mm')}
                      />
                      <Tag color={getStatusColor(item.status)}>
                        {getStatusText(item.status)}
                      </Tag>
                    </List.Item>
                  )}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: 24, color: '#999' }}>
                  暂无报名记录
                </div>
              )}
            </Card>
          </Col>
        )}
      </Row>
    </div>
  )
}

export default Dashboard
