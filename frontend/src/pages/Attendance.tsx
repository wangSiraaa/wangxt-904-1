import { useState, useEffect } from 'react'
import { Table, Button, Space, message, Tag, Tabs, Card, Row, Col } from 'antd'
import { LoginOutlined, LogoutOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { attendanceApi, shiftApi } from '../api'
import dayjs from 'dayjs'

function Attendance() {
  const [myAttendances, setMyAttendances] = useState<any[]>([])
  const [shifts, setShifts] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [activeTab, setActiveTab] = useState('my')

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const userStr = localStorage.getItem('user')
      const currentUser = userStr ? JSON.parse(userStr) : null

      if (currentUser?.role === 'volunteer') {
        const res = await attendanceApi.my()
        setMyAttendances(res.data)
      }

      const shiftsRes = await shiftApi.list({ status: 'published' })
      setShifts(shiftsRes.data)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCheckIn = async (shiftId: number) => {
    try {
      await attendanceApi.checkIn(shiftId)
      message.success('签到成功')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '签到失败')
    }
  }

  const handleCheckOut = async (shiftId: number) => {
    try {
      await attendanceApi.checkOut(shiftId)
      message.success('签退成功')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '签退失败')
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      not_checked_in: 'default',
      present: 'green',
      late: 'orange',
      absent: 'red',
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      not_checked_in: '未签到',
      present: '已签到',
      late: '迟到',
      absent: '缺勤',
    }
    return texts[status] || status
  }

  const todayShifts = shifts.filter(s => dayjs(s.shift_date).isSame(dayjs(), 'day'))

  const myColumns = [
    {
      title: '班次',
      key: 'shift',
      render: (_: any, record: any) => (
        <div>
          <div>{record.shift?.study_room?.name || '-'}</div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {dayjs(record.shift?.shift_date).format('YYYY-MM-DD')}
          </div>
        </div>
      ),
    },
    {
      title: '时段',
      key: 'time',
      render: (_: any, record: any) => (
        <span>
          {record.shift?.start_time?.slice(0, 5)} - {record.shift?.end_time?.slice(0, 5)}
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '签到时间',
      dataIndex: 'check_in_time',
      key: 'check_in',
      render: (t: string) => t ? dayjs(t).format('HH:mm:ss') : '-',
    },
    {
      title: '签退时间',
      dataIndex: 'check_out_time',
      key: 'check_out',
      render: (t: string) => t ? dayjs(t).format('HH:mm:ss') : '-',
    },
    {
      title: '时长(小时)',
      dataIndex: 'duration_hours',
      key: 'duration',
    },
  ]

  const todayColumns = [
    {
      title: '书房',
      dataIndex: ['study_room', 'name'],
      key: 'room',
      render: (_: any, record: any) => record.study_room?.name || '-',
    },
    {
      title: '时段',
      key: 'time',
      render: (_: any, record: any) => (
        <span>
          {record.start_time?.slice(0, 5)} - {record.end_time?.slice(0, 5)}
        </span>
      ),
    },
    {
      title: '班次类型',
      dataIndex: 'shift_type',
      key: 'type',
      render: (type: string) => {
        const colors: Record<string, string> = { morning: 'gold', afternoon: 'cyan', night: 'purple' }
        const texts: Record<string, string> = { morning: '早班', afternoon: '午班', night: '晚班' }
        return <Tag color={colors[type]}>{texts[type]}</Tag>
      },
    },
    {
      title: '人数',
      key: 'count',
      render: (_: any, record: any) => `${record.current_volunteers}/${record.max_volunteers}`,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => {
        const hasCheckedIn = myAttendances.some(
          a => a.shift_id === record.id && a.status !== 'not_checked_in'
        )
        const hasCheckedOut = myAttendances.some(
          a => a.shift_id === record.id && a.check_out_time
        )

        if (hasCheckedOut) {
          return <Tag color="green">已完成</Tag>
        }
        if (hasCheckedIn) {
          return (
            <Button type="primary" size="small" icon={<LogoutOutlined />} onClick={() => handleCheckOut(record.id)}>
              签退
            </Button>
          )
        }
        return (
          <Button size="small" icon={<LoginOutlined />} onClick={() => handleCheckIn(record.id)}>
            签到
          </Button>
        )
      },
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>签到签退</h2>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#999' }}>今日班次</div>
            <div style={{ fontSize: 24, fontWeight: 'bold' }}>{todayShifts.length}</div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#999' }}>已签到</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
              {myAttendances.filter(a => a.status === 'present' || a.status === 'late').length}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#999' }}>累计时长</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
              {myAttendances.reduce((sum, a) => sum + (a.duration_hours || 0), 0).toFixed(1)}h
            </div>
          </Card>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'today',
            label: '今日签到',
            children: (
              <Table
                rowKey="id"
                columns={todayColumns}
                dataSource={todayShifts}
                loading={loading}
                pagination={false}
              />
            ),
          },
          {
            key: 'my',
            label: '我的记录',
            children: (
              <Table
                rowKey="id"
                columns={myColumns}
                dataSource={myAttendances}
                loading={loading}
                pagination={{ pageSize: 10 }}
              />
            ),
          },
        ]}
      />
    </div>
  )
}

export default Attendance
