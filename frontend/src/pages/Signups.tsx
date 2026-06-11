import { useState, useEffect } from 'react'
import { Table, Button, Space, message, Tag, Modal, Select, Alert, Popconfirm } from 'antd'
import { CheckOutlined, CloseOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { signupApi, volunteerApi, shiftApi } from '../api'
import dayjs from 'dayjs'

function Signups() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [detailModal, setDetailModal] = useState(false)
  const [selectedSignup, setSelectedSignup] = useState<any>(null)

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
      const res = await signupApi.list()
      setData(res.data)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const canReview = user && (user.role === 'admin' || user.role === 'operations')
  const isVolunteer = user?.role === 'volunteer'

  const handleApprove = async (id: number) => {
    try {
      await signupApi.approve(id)
      message.success('审核通过')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '审核失败')
    }
  }

  const handleReject = async (id: number) => {
    Modal.confirm({
      title: '拒绝原因',
      content: (
        <Select
          placeholder="请选择或输入拒绝原因"
          style={{ width: '100%' }}
          mode="tags"
          options={[
            { value: '培训未完成', label: '培训未完成' },
            { value: '排班冲突', label: '排班冲突' },
            { value: '人数已满', label: '人数已满' },
            { value: '其他原因', label: '其他原因' },
          ]}
          onChange={(val) => {
            if (val && val.length > 0) {
              signupApi.reject(id, val[val.length - 1]).then(() => {
                message.success('已拒绝')
                loadData()
              }).catch((e: any) => {
                message.error(e.response?.data?.detail || '操作失败')
              })
            }
          }}
        />
      ),
      okText: '确认拒绝',
      cancelText: '取消',
    })
  }

  const handleCancel = async (id: number) => {
    try {
      await signupApi.cancel(id)
      message.success('已取消报名')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '取消失败')
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'orange',
      approved: 'green',
      rejected: 'red',
      cancelled: 'default',
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待审核',
      approved: '已通过',
      rejected: '已拒绝',
      cancelled: '已取消',
    }
    return texts[status] || status
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '志愿者',
      dataIndex: ['volunteer', 'name'],
      key: 'volunteer',
      render: (_: any, record: any) => record.volunteer?.name || '-',
    },
    {
      title: '班次信息',
      key: 'shift',
      render: (_: any, record: any) => (
        <div>
          <div>
            <Tag color="blue">{record.shift?.study_room?.name || '-'}</Tag>
            <Tag>{dayjs(record.shift?.shift_date).format('MM-DD')}</Tag>
          </div>
          <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
            {record.shift?.start_time?.slice(0, 5)} - {record.shift?.end_time?.slice(0, 5)}
            {' | '}
            {record.shift?.shift_type === 'morning' ? '早班' : record.shift?.shift_type === 'afternoon' ? '午班' : '晚班'}
          </div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '报名时间',
      dataIndex: 'signup_time',
      key: 'signup_time',
      width: 160,
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '审核人',
      dataIndex: ['reviewer', 'name'],
      key: 'reviewer',
      width: 80,
      render: (_: any, record: any) => record.reviewer?.name || '-',
    },
  ]

  if (canReview || isVolunteer) {
    columns.push({
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: any) => (
        <Space size="small">
          {canReview && record.status === 'pending' && (
            <>
              <Button type="primary" size="small" icon={<CheckOutlined />} onClick={() => handleApprove(record.id)}>
                通过
              </Button>
              <Button size="small" danger icon={<CloseOutlined />} onClick={() => handleReject(record.id)}>
                拒绝
              </Button>
            </>
          )}
          {isVolunteer && (record.status === 'pending' || record.status === 'approved') && (
            <Popconfirm title="确定要取消报名吗？" onConfirm={() => handleCancel(record.id)}>
              <Button size="small" danger>
                取消
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    })
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>报名记录</h2>
      </div>

      {data.some(s => s.status === 'pending') && canReview && (
        <Alert
          message={`有 ${data.filter(s => s.status === 'pending').length} 条报名待审核`}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}

export default Signups
