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

import io.airlift.slice.Slice;
import io.airlift.slice.Slices;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.Assert.assertEquals;
import static org.junit.jupiter.api.TestInstance.Lifecycle.PER_CLASS;

@TestInstance(PER_CLASS)
public class GunzipFunctionsTest
{
    private static final String NULL_VALUE = "<null>";

    @Test
    public void testValidateSucess()
    {
        String expectedValue = "{"
                + "\"server\":\"thrift://hive-metastore:9083\","
                + "\"servicePrincipal\":\"\","
                + "\"db\":\"flight_db\","
                + "\"dbJson\":\"{\\\"1\\\":{\\\"str\\\":\\\"flight_db\\\"},"
                + "\\\"3\\\":{\\\"str\\\":\\\"file:/user/hive/warehouse/flight_db.db\\\"},"
                + "\\\"4\\\":{\\\"map\\\":[\\\"str\\\",\\\"str\\\",1,"
                + "{\\\"trino_query_id\\\":\\\"20250804_135929_00000_ug6h6\\\"}]},"
                + "\\\"6\\\":{\\\"str\\\":\\\"trino\\\"},"
                + "\\\"7\\\":{\\\"i32\\\":1},"
                + "\\\"8\\\":{\\\"str\\\":\\\"hive\\\"},"
                + "\\\"9\\\":{\\\"i32\\\":1754315969}}\","
                + "\"timestamp\":1754315969"
                + "}";
        Slice sliceValue = Slices.utf8Slice("H4sIAAAAAAAAAF1Q23KDIBD9F55tAFEjfEKe+h46DE1I2BmNFjCdTsZ/76JNO9aXPZzL7hkfJLpwd4EoknyAS1KUeri7l94lG9MQnJKsFaRYfHByrwFuJxhthwlkz+84Lx1cfTKIM3GIww3JhyZcE4UjpoBA/9k0mQtNxD8VOqfohGeWAvTTBucHfNPf3O4ZrdZob0cEx58dxXPyArWEPQfzMbnwZeC8XChZWbOWVYaLWpbSsPyZ6dr4Bte+5cXNttOyZD25XxUQJQKemXbrzaVXq9xY93UleC0bOc/4exL0LibbjxvlGzwTdlWGAQAA");
        String value = GunzipFunctions.gunzipBase64(sliceValue).toStringUtf8();
        assertThat(value).isNotNull();
        assertEquals(expectedValue, value);
    }
}
