import { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Table, message } from 'antd'
import {
  BankOutlined,
  CalendarOutlined,
  TeamOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  AlertOutlined
} from '@ant-design/icons'
import { statsApi } from '../api'

function Statistics() {
  const [overview, setOverview] = useState<any>(null)
  const [volunteerHours, setVolunteerHours] = useState<any[]>([])
  const [roomUsage, setRoomUsage] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [overviewRes, hoursRes, usageRes] = await Promise.all([
        statsApi.overview(),
        statsApi.volunteerHours(),
        statsApi.roomUsage(),
      ])
      setOverview(overviewRes.data)
      setVolunteerHours(hoursRes.data)
      setRoomUsage(usageRes.data)
    } catch (error) {
      message.error('加载统计数据失败')
    } finally {
      setLoading(false)
    }
  }

  const hoursColumns = [
    { title: '志愿者', dataIndex: 'name', key: 'name' },
    { title: '服务班次', dataIndex: 'shift_count', key: 'shift_count', width: 120 },
    {
      title: '累计时长(小时)',
      dataIndex: 'total_hours',
      key: 'total_hours',
      width: 140,
      render: (h: number) => h.toFixed(2),
      sorter: (a: any, b: any) => a.total_hours - b.total_hours,
    },
  ]

  const usageColumns = [
    { title: '书房', dataIndex: 'name', key: 'name' },
    {
      title: '班次数',
      dataIndex: 'total_shifts',
      key: 'total_shifts',
      width: 120,
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>运营统计</h2>

      {overview && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="书房点位"
                value={overview.total_rooms}
                prefix={<BankOutlined style={{ color: '#1890ff' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总班次"
                value={overview.total_shifts}
                prefix={<CalendarOutlined style={{ color: '#52c41a' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="志愿者人数"
                value={overview.total_volunteers}
                prefix={<TeamOutlined style={{ color: '#faad14' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总报名数"
                value={overview.total_signups}
                prefix={<FileTextOutlined style={{ color: '#722ed1' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="已完成班次"
                value={overview.completed_shifts}
                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="待审核报名"
                value={overview.pending_signups}
                prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
                valueStyle={{ color: overview.pending_signups > 0 ? '#faad14' : undefined }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="待审核请假"
                value={overview.pending_leaves}
                prefix={<AlertOutlined style={{ color: '#f5222d' }} />}
                valueStyle={{ color: overview.pending_leaves > 0 ? '#f5222d' : undefined }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="补位待办"
                value={overview.replacement_todos}
                prefix={<AlertOutlined style={{ color: '#faad14' }} />}
                valueStyle={{ color: overview.replacement_todos > 0 ? '#faad14' : undefined }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title="志愿者服务时长排行" loading={loading}>
            <Table
              rowKey="volunteer_id"
              columns={hoursColumns}
              dataSource={volunteerHours}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="书房使用情况" loading={loading}>
            <Table
              rowKey="room_id"
              columns={usageColumns}
              dataSource={roomUsage}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Statistics
