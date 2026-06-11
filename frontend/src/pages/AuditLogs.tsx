import { useState, useEffect } from 'react'
import { Table, message, Tag, Select, Input } from 'antd'
import { auditApi } from '../api'
import dayjs from 'dayjs'

function AuditLogs() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await auditApi.list()
      setData(res.data)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const getActionColor = (action: string) => {
    if (action.includes('create') || action.includes('approve') || action.includes('publish')) return 'green'
    if (action.includes('delete') || action.includes('reject') || action.includes('cancel')) return 'red'
    if (action.includes('update') || action.includes('check')) return 'blue'
    return 'default'
  }

  const getEntityTypeText = (type: string) => {
    const texts: Record<string, string> = {
      study_room: '书房点位',
      shift: '班次',
      signup: '报名',
      attendance: '签到',
      leave: '请假',
      volunteer: '志愿者',
      replacement: '补位',
    }
    return texts[type] || type
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 150,
      render: (action: string) => <Tag color={getActionColor(action)}>{action}</Tag>,
    },
    {
      title: '用户',
      dataIndex: ['user', 'name'],
      key: 'user',
      width: 100,
      render: (_: any, record: any) => record.user?.name || '系统',
    },
    {
      title: '实体类型',
      dataIndex: 'entity_type',
      key: 'entity_type',
      width: 100,
      render: (type: string) => type ? getEntityTypeText(type) : '-',
    },
    { title: '实体ID', dataIndex: 'entity_id', key: 'entity_id', width: 80 },
    {
      title: '详情',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip',
      width: 120,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm:ss'),
    },
  ]

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>审计日志</h2>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 20 }}
      />
    </div>
  )
}

export default AuditLogs
