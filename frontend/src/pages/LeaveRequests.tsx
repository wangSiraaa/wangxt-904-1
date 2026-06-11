import { useState, useEffect } from 'react'
import {
  Table, Button, Space, message, Tag, Modal, Input, Tabs,
  Form, Select, Popconfirm, Alert
} from 'antd'
import { PlusOutlined, CheckOutlined, CloseOutlined, UserAddOutlined } from '@ant-design/icons'
import { leaveApi, volunteerApi, shiftApi } from '../api'
import dayjs from 'dayjs'

function LeaveRequests() {
  const [data, setData] = useState<any[]>([])
  const [replacements, setReplacements] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [assignModalVisible, setAssignModalVisible] = useState(false)
  const [selectedTodoId, setSelectedTodoId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [volunteers, setVolunteers] = useState<any[]>([])
  const [shifts, setShifts] = useState<any[]>([])

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
    loadData()
    loadVolunteers()
    loadShifts()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await leaveApi.list()
      setData(res.data)

      const todoRes = await leaveApi.listReplacements()
      setReplacements(todoRes.data)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const loadVolunteers = async () => {
    try {
      const res = await volunteerApi.list()
      setVolunteers(res.data)
    } catch (error) {
      // ignore
    }
  }

  const loadShifts = async () => {
    try {
      const res = await shiftApi.list({ status: 'published' })
      setShifts(res.data)
    } catch (error) {
      // ignore
    }
  }

  const canReview = user && (user.role === 'admin' || user.role === 'operations')
  const isVolunteer = user?.role === 'volunteer'

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      await leaveApi.create(values)
      message.success('请假申请已提交')
      setModalVisible(false)
      loadData()
    } catch (error: any) {
      if (error?.response?.data?.detail) {
        message.error(error.response.data.detail)
      }
    }
  }

  const handleApprove = async (id: number) => {
    try {
      await leaveApi.approve(id)
      message.success('已批准请假')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const handleReject = async (id: number) => {
    Modal.confirm({
      title: '拒绝原因',
      content: (
        <Select
          placeholder="请选择拒绝原因"
          style={{ width: '100%' }}
          mode="tags"
          options={[
            { value: '理由不充分', label: '理由不充分' },
            { value: '班次重要', label: '班次重要' },
            { value: '其他原因', label: '其他原因' },
          ]}
          onChange={(val) => {
            if (val && val.length > 0) {
              leaveApi.reject(id, val[val.length - 1]).then(() => {
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

  const handleAssign = (todoId: number) => {
    setSelectedTodoId(todoId)
    setAssignModalVisible(true)
  }

  const handleAssignSubmit = async (volunteerId: number) => {
    if (!selectedTodoId) return
    try {
      await leaveApi.assignReplacement(selectedTodoId, volunteerId)
      message.success('已分配补位')
      setAssignModalVisible(false)
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '分配失败')
    }
  }

  const handleComplete = async (todoId: number) => {
    try {
      await leaveApi.completeReplacement(todoId)
      message.success('补位完成')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'orange',
      approved: 'green',
      rejected: 'red',
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待审核',
      approved: '已批准',
      rejected: '已拒绝',
    }
    return texts[status] || status
  }

  const getTodoStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'red',
      assigned: 'orange',
      completed: 'green',
    }
    return colors[status] || 'default'
  }

  const getTodoStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待处理',
      assigned: '已分配',
      completed: '已完成',
    }
    return texts[status] || status
  }

  const leaveColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '志愿者',
      dataIndex: ['volunteer', 'name'],
      key: 'volunteer',
      render: (_: any, record: any) => record.volunteer?.name || '-',
    },
    {
      title: '班次',
      key: 'shift',
      render: (_: any, record: any) => (
        <div>
          <div>{record.shift?.study_room?.name || '-'}</div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {dayjs(record.shift?.shift_date).format('MM-DD')} {record.shift?.start_time?.slice(0, 5)}
          </div>
        </div>
      ),
    },
    { title: '原因', dataIndex: 'reason', key: 'reason', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (s: string) => <Tag color={getStatusColor(s)}>{getStatusText(s)}</Tag>,
    },
    {
      title: '申请时间',
      dataIndex: 'request_time',
      key: 'request_time',
      width: 160,
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '补位',
      dataIndex: 'replacement_assigned',
      key: 'replacement',
      width: 80,
      render: (assigned: boolean) => (
        assigned ? <Tag color="green">已分配</Tag> : <Tag color="orange">待补位</Tag>
      ),
    },
  ]

  if (canReview) {
    leaveColumns.push({
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: any) => (
        <Space size="small">
          {record.status === 'pending' && (
            <>
              <Button type="primary" size="small" icon={<CheckOutlined />} onClick={() => handleApprove(record.id)}>
                批准
              </Button>
              <Button size="small" danger icon={<CloseOutlined />} onClick={() => handleReject(record.id)}>
                拒绝
              </Button>
            </>
          )}
        </Space>
      ),
    })
  }

  const todoColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '班次',
      key: 'shift',
      render: (_: any, record: any) => (
        <div>
          <div>{record.shift?.study_room?.name || '-'}</div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {dayjs(record.shift?.shift_date).format('MM-DD')} {record.shift?.start_time?.slice(0, 5)}
          </div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (s: string) => <Tag color={getTodoStatusColor(s)}>{getTodoStatusText(s)}</Tag>,
    },
    {
      title: '分配给',
      dataIndex: ['assignee', 'name'],
      key: 'assignee',
      render: (_: any, record: any) => record.assignee?.name || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm'),
    },
  ]

  if (canReview) {
    todoColumns.push({
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: any) => (
        <Space size="small">
          {record.status === 'pending' && (
            <Button type="primary" size="small" icon={<UserAddOutlined />} onClick={() => handleAssign(record.id)}>
              分配
            </Button>
          )}
          {record.status === 'assigned' && record.assigned_to === user?.id && (
            <Button type="primary" size="small" onClick={() => handleComplete(record.id)}>
              完成补位
            </Button>
          )}
        </Space>
      ),
    })
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>请假补位</h2>
        {isVolunteer && (
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setModalVisible(true) }}>
            申请请假
          </Button>
        )}
      </div>

      {replacements.filter(r => r.status === 'pending').length > 0 && canReview && (
        <Alert
          message={`有 ${replacements.filter(r => r.status === 'pending').length} 个补位待办需要处理`}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Tabs
        items={[
          {
            key: 'leave',
            label: '请假申请',
            children: (
              <Table
                rowKey="id"
                columns={leaveColumns}
                dataSource={data}
                loading={loading}
                pagination={{ pageSize: 10 }}
              />
            ),
          },
          {
            key: 'replacements',
            label: `补位待办 (${replacements.filter(r => r.status === 'pending').length})`,
            children: (
              <Table
                rowKey="id"
                columns={todoColumns}
                dataSource={replacements}
                loading={loading}
                pagination={{ pageSize: 10 }}
              />
            ),
          },
        ]}
      />

      <Modal
        title="申请请假"
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={500}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="shift_id" label="选择班次" rules={[{ required: true, message: '请选择班次' }]}>
            <Select placeholder="请选择班次">
              {shifts.map(shift => (
                <Select.Option key={shift.id} value={shift.id}>
                  {shift.study_room?.name} - {dayjs(shift.shift_date).format('MM-DD')} {shift.start_time?.slice(0, 5)}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="reason" label="请假原因" rules={[{ required: true, message: '请输入原因' }]}>
            <Input.TextArea rows={4} placeholder="请输入请假原因" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="分配补位"
        open={assignModalVisible}
        onCancel={() => setAssignModalVisible(false)}
        footer={null}
        width={500}
      >
        <Select
          placeholder="请选择补位志愿者"
          style={{ width: '100%' }}
          showSearch
          filterOption={(input, option) =>
            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
          }
          options={volunteers.map(v => ({
            label: `${v.name} (${v.volunteer_profile?.training_status === 'completed' ? '已培训' : '未培训'})`,
            value: v.id,
          }))}
          onSelect={handleAssignSubmit}
        />
      </Modal>
    </div>
  )
}

export default LeaveRequests
