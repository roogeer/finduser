<template>
  <div class="hello">
    <h3>查询结果</h3>
	<table class="table_head" border="1px" align="center">
		<thead>
			<tr>
				<th width="30px" rowspan="2">SN</th>
				<th width="108px" rowspan="2">用户帐号</th>
				<th width="384px" colspan="3">OLT</th>
				<th rowspan="2">Vlan</th>
				<th rowspan="2">nasportid</th>
				<th rowspan="2">备注</th>
			</tr>
			<tr>
				<th width="128px">名称</th>
				<th width="128px">IP</th>
				<th width="128px">ONU</th>
			</tr>
		</thead>
		<tbody>
		</tbody>
	</table>
  </div>
</template>

<script>
	
export default {
  name: 'UserList',
  props: {
	users: Array
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.table_head {
	border-collapse: collapse;
	margin: 10px auto;
	height: 100%;
	width:  1500px;
	padding: 0;
	/*vertical-align: bottom;*/
	}

th {
	text-align:center;
	background-color:#337ab7;
	color:#FFFFFF;
}
	
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>

