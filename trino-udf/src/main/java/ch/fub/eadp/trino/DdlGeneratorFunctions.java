/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package ch.fub.eadp.trino;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.trino.spi.function.Description;
import io.trino.spi.function.ScalarFunction;
import io.trino.spi.function.SqlType;

import static io.trino.spi.type.StandardTypes.VARCHAR;

public class DdlGeneratorFunctions
{
    private DdlGeneratorFunctions() {}

    @Description("Generates a CREATE TABLE DDL statement from JSON")
    @ScalarFunction("generate_ddl_from_json")
    @SqlType(VARCHAR)
    public static String generateDdlFromJson(@SqlType(VARCHAR) String json)
    {
        try {
            ObjectMapper mapper = new ObjectMapper();
            JsonNode root = mapper.readTree(json);

            String dbName = root.path("dbName").asText();
            String tableName = root.path("tableName").asText();
            JsonNode columns = root.path("sd").path("cols");
            JsonNode partitions = root.path("partitionKeys");
            String location = root.path("sd").path("location").asText();
            String inputFormat = root.path("sd").path("inputFormat").asText();
            String serde = root.path("sd").path("serdeInfo").path("serializationLib").asText();

            StringBuilder ddl = new StringBuilder();

            ddl.append("CREATE EXTERNAL TABLE IF NOT EXISTS ")
                    .append(dbName).append(".").append(tableName)
                    .append(" (\n");

            // Add columns
            for (int i = 0; i < columns.size(); i++) {
                JsonNode col = columns.get(i);
                ddl.append("  ")
                        .append(col.path("name").asText())
                        .append(" ")
                        .append(col.path("type").asText());
                if (i < columns.size() - 1) {
                    ddl.append(",");
                }
                ddl.append("\n");
            }

            ddl.append(")\n");

            // Add partition columns if any
            if (partitions != null && partitions.size() > 0) {
                ddl.append("PARTITIONED BY (\n");
                for (int i = 0; i < partitions.size(); i++) {
                    JsonNode part = partitions.get(i);
                    ddl.append("  ")
                            .append(part.path("name").asText())
                            .append(" ")
                            .append(part.path("type").asText());
                    if (i < partitions.size() - 1) {
                        ddl.append(",");
                    }
                    ddl.append("\n");
                }
                ddl.append(")\n");
            }

            ddl.append("STORED AS ")
                    .append(inputFormat.contains("parquet") ? "PARQUET" : "TEXTFILE")
                    .append("\n");

            ddl.append("LOCATION '")
                    .append(location)
                    .append("'\n");

            if (serde != null && !serde.isEmpty()) {
                ddl.append("ROW FORMAT SERDE '")
                        .append(serde)
                        .append("'\n");
            }

            ddl.append(";");

            return ddl.toString();
        }
        catch (Exception e) {
            return "ERROR: " + e.getMessage();
        }
    }
}
