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

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.airlift.slice.Slice;
import io.airlift.slice.Slices;
import io.trino.spi.function.Description;
import io.trino.spi.function.ScalarFunction;
import io.trino.spi.function.SqlType;
import org.apache.hadoop.hive.metastore.api.Table;
import org.apache.thrift.TDeserializer;
import org.apache.thrift.TException;
import org.apache.thrift.protocol.TJSONProtocol;
import org.apache.thrift.transport.TTransportException;

import java.nio.charset.Charset;

public class HiveMetastoreFunctions
{
    private HiveMetastoreFunctions() {}

    @ScalarFunction("to_json")
    @Description("Returns JSON")
    @SqlType("varchar")
    public static Slice toJson(@SqlType("varchar") Slice input)
    {
        Table table = new Table();  // Replace with your Thrift type
        String jsonValue = null;

        TDeserializer deserializer = null;
        try {
            deserializer = new TDeserializer(new TJSONProtocol.Factory());
            String value = input.toStringUtf8();
            deserializer.deserialize(table, value.getBytes(Charset.defaultCharset()));

            ObjectMapper mapper = new ObjectMapper();
            //jsonValue = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(table);
            jsonValue = mapper.writeValueAsString(table);
        }
        catch (TTransportException e) {
            throw new RuntimeException(e);
        }
        catch (TException e) {
            throw new RuntimeException(e);
        }
        catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }

        return Slices.utf8Slice(jsonValue);
    }
}
